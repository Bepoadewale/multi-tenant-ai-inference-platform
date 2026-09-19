variable "enable_gpu_nodes" {
  type        = bool
  default     = false
  description = "Explicit cost safety switch; no GPU nodes by default."
}

variable "gpu_instance_types" {
  type    = list(string)
  default = ["g5.xlarge"]
}
