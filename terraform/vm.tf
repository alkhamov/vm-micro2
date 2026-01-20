resource "google_compute_instance" "camunda_vm" {
  name         = "camunda-free-tier"
  machine_type = "e2-micro"
  zone         = "us-central1-a"

  tags = ["camunda"]

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-12"
      type  = "pd-standard"
      size  = 30
    }
  }

  network_interface {
    network = "default"

    access_config {
      # ephemeral external IP ONLY
    }
  }

  metadata = {
    startup-script = templatefile("${path.module}/startup.sh", {
      vm_user  = var.vm_user
      timezone = var.timezone
    })
  }

  scheduling {
    automatic_restart = false
    preemptible       = false
  }

  service_account {
    scopes = ["cloud-platform"]
  }

  labels = {
    purpose = "camunda-dev"
    tier    = "free"
  }
}
