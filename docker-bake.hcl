// Targets filled by GitHub Actions: one for the regular tag
target "docker-metadata-action" {}

// This sets the platforms and is further extended by GitHub Actions to set the
// output and the cache locations
target "base" {
  platforms = [
    "linux/amd64",
    // "linux/arm64",
  ]
}

// Top-level target to build the matrix-tools container image
target "matrix-tools" {
  inherits = ["base", "docker-metadata-action"]
  dockerfile = "Dockerfile"
  context = "./matrix-tools"
}
