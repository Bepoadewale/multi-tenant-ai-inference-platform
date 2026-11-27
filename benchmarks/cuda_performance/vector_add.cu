#include <cuda_runtime.h>

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstddef>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>

__global__ void vector_add(const float* left, const float* right, float* output,
                           std::size_t count) {
  const std::size_t index = blockIdx.x * blockDim.x + threadIdx.x;
  if (index < count) {
    output[index] = left[index] + right[index];
  }
}

void check_cuda(cudaError_t status, const char* operation) {
  if (status != cudaSuccess) {
    throw std::runtime_error(std::string(operation) + ": " + cudaGetErrorString(status));
  }
}

double median(std::vector<double> values) {
  std::sort(values.begin(), values.end());
  const std::size_t middle = values.size() / 2;
  if (values.size() % 2 == 0) {
    return (values[middle - 1] + values[middle]) / 2.0;
  }
  return values[middle];
}

int main(int argc, char** argv) {
  try {
    const std::size_t count = argc > 1 ? std::stoull(argv[1]) : (1U << 20);
    const int warmups = argc > 2 ? std::stoi(argv[2]) : 5;
    const int repeats = argc > 3 ? std::stoi(argv[3]) : 20;
    if (count == 0 || count > (1U << 22) || warmups < 0 || warmups > 20 || repeats < 1 || repeats > 100) {
      throw std::invalid_argument("usage: vector_add [elements:1..4194304] [warmups:0..20] [repeats:1..100]");
    }

    int device_count = 0;
    check_cuda(cudaGetDeviceCount(&device_count), "cudaGetDeviceCount");
    if (device_count != 1) {
      throw std::runtime_error("expected exactly one visible NVIDIA GPU");
    }
    cudaDeviceProp properties{};
    check_cuda(cudaGetDeviceProperties(&properties, 0), "cudaGetDeviceProperties");
    if (std::string(properties.name).find("L4") == std::string::npos) {
      throw std::runtime_error(std::string("expected NVIDIA L4, observed ") + properties.name);
    }

    std::vector<float> left(count), right(count), cpu_output(count), gpu_output(count);
    std::iota(left.begin(), left.end(), 0.0F);
    std::fill(right.begin(), right.end(), 2.0F);
    std::vector<double> cpu_samples;
    for (int iteration = 0; iteration < warmups + repeats; ++iteration) {
      const auto start = std::chrono::steady_clock::now();
      for (std::size_t index = 0; index < count; ++index) {
        cpu_output[index] = left[index] + right[index];
      }
      const auto stop = std::chrono::steady_clock::now();
      if (iteration >= warmups) {
        cpu_samples.push_back(std::chrono::duration<double, std::milli>(stop - start).count());
      }
    }

    float *device_left = nullptr, *device_right = nullptr, *device_output = nullptr;
    const std::size_t bytes = count * sizeof(float);
    check_cuda(cudaMalloc(reinterpret_cast<void**>(&device_left), bytes), "cudaMalloc left");
    check_cuda(cudaMalloc(reinterpret_cast<void**>(&device_right), bytes), "cudaMalloc right");
    check_cuda(cudaMalloc(reinterpret_cast<void**>(&device_output), bytes), "cudaMalloc output");
    cudaEvent_t transfer_start, transfer_stop, kernel_start, kernel_stop;
    check_cuda(cudaEventCreate(&transfer_start), "cudaEventCreate transfer start");
    check_cuda(cudaEventCreate(&transfer_stop), "cudaEventCreate transfer stop");
    check_cuda(cudaEventCreate(&kernel_start), "cudaEventCreate kernel start");
    check_cuda(cudaEventCreate(&kernel_stop), "cudaEventCreate kernel stop");

    check_cuda(cudaEventRecord(transfer_start), "record H2D start");
    check_cuda(cudaMemcpy(device_left, left.data(), bytes, cudaMemcpyHostToDevice), "copy left to GPU");
    check_cuda(cudaMemcpy(device_right, right.data(), bytes, cudaMemcpyHostToDevice), "copy right to GPU");
    check_cuda(cudaEventRecord(transfer_stop), "record H2D stop");
    check_cuda(cudaEventSynchronize(transfer_stop), "wait for H2D copies");
    float host_to_device_ms = 0.0F;
    check_cuda(cudaEventElapsedTime(&host_to_device_ms, transfer_start, transfer_stop), "measure H2D");

    const int threads = 256;
    const int blocks = static_cast<int>((count + threads - 1) / threads);
    for (int iteration = 0; iteration < warmups; ++iteration) {
      vector_add<<<blocks, threads>>>(device_left, device_right, device_output, count);
      check_cuda(cudaGetLastError(), "launch warmup vector_add");
    }
    check_cuda(cudaDeviceSynchronize(), "synchronize warmup kernels");

    std::vector<double> gpu_samples;
    for (int iteration = 0; iteration < repeats; ++iteration) {
      check_cuda(cudaEventRecord(kernel_start), "record kernel start");
      vector_add<<<blocks, threads>>>(device_left, device_right, device_output, count);
      check_cuda(cudaGetLastError(), "launch vector_add");
      check_cuda(cudaEventRecord(kernel_stop), "record kernel stop");
      check_cuda(cudaEventSynchronize(kernel_stop), "wait for vector_add");
      float elapsed_ms = 0.0F;
      check_cuda(cudaEventElapsedTime(&elapsed_ms, kernel_start, kernel_stop), "measure vector_add");
      gpu_samples.push_back(elapsed_ms);
    }

    check_cuda(cudaEventRecord(transfer_start), "record D2H start");
    check_cuda(cudaMemcpy(gpu_output.data(), device_output, bytes, cudaMemcpyDeviceToHost), "copy output to host");
    check_cuda(cudaEventRecord(transfer_stop), "record D2H stop");
    check_cuda(cudaEventSynchronize(transfer_stop), "wait for D2H copy");
    float device_to_host_ms = 0.0F;
    check_cuda(cudaEventElapsedTime(&device_to_host_ms, transfer_start, transfer_stop), "measure D2H");

    for (std::size_t index = 0; index < count; ++index) {
      if (std::abs(gpu_output[index] - cpu_output[index]) > 1e-6F) {
        throw std::runtime_error("CPU/GPU correctness comparison failed");
      }
    }

    const double gpu_median_ms = median(gpu_samples);
    const double effective_gb_s = (3.0 * bytes / (gpu_median_ms / 1000.0)) / 1e9;
    std::cout << std::fixed << std::setprecision(6)
              << "{\"gpu\":\"" << properties.name << "\",\"elements\":" << count
              << ",\"warmups\":" << warmups << ",\"repeats\":" << repeats
              << ",\"cpu_median_ms\":" << median(cpu_samples)
              << ",\"gpu_kernel_median_ms\":" << gpu_median_ms
              << ",\"effective_memory_gb_s\":" << effective_gb_s
              << ",\"host_to_device_ms\":" << host_to_device_ms
              << ",\"device_to_host_ms\":" << device_to_host_ms
              << ",\"correctness\":\"passed\"}\n";

    check_cuda(cudaEventDestroy(transfer_start), "destroy transfer start event");
    check_cuda(cudaEventDestroy(transfer_stop), "destroy transfer stop event");
    check_cuda(cudaEventDestroy(kernel_start), "destroy kernel start event");
    check_cuda(cudaEventDestroy(kernel_stop), "destroy kernel stop event");
    check_cuda(cudaFree(device_left), "free left");
    check_cuda(cudaFree(device_right), "free right");
    check_cuda(cudaFree(device_output), "free output");
    return 0;
  } catch (const std::exception& error) {
    std::cerr << "CUDA vector-add experiment failed: " << error.what() << '\n';
    return 1;
  }
}
