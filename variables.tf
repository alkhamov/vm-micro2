variable "project_id" {
  type        = string
  description = "GCP project ID"
}

variable "vm_user" {
  type        = string
  description = "Linux username"
  default     = "alkhamov"
}

variable "timezone" {
  type        = string
  default     = "UTC"
}
