#!/usr/bin/env bash
set -e

# JPAMB Docker Build Script
# Builds and manages the Docker image using Nix

cd "$(dirname "$0")/.."

# Detect container runtime (docker or podman)
if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
    CONTAINER_CMD="docker"
elif command -v podman >/dev/null 2>&1; then
    CONTAINER_CMD="podman"
else
    echo "Error: Neither docker nor podman is available"
    exit 1
fi

echo "Using container runtime: $CONTAINER_CMD"

usage() {
    cat << EOF
Usage: $0 [COMMAND]

Commands:
    build    Build the Docker image with Nix
    load     Load the image into Docker
    test     Test the Docker image
    run      Run an interactive container
    export   Export image as tarball

Examples:
    ./scripts/build-docker.sh build
    ./scripts/build-docker.sh load
    ./scripts/build-docker.sh run
EOF
}

build_image() {
    echo "Building Docker image with Nix..."
    nix build .#packages.x86_64-linux.default --print-build-logs
    echo "Docker image built successfully!"
    echo "Image location: $(readlink -f result)"
}

load_image() {
    if [ ! -f result ]; then
        echo "No built image found. Run 'build' first."
        exit 1
    fi

    echo "Loading Docker image..."
    $CONTAINER_CMD load < result

    IMAGE_NAME=$($CONTAINER_CMD images --format "{{.Repository}}:{{.Tag}}" | grep jpamb | head -1)
    echo "Image loaded: $IMAGE_NAME"
}

test_image() {
    IMAGE_NAME=$($CONTAINER_CMD images --format "{{.Repository}}:{{.Tag}}" | grep jpamb | head -1)

    if [ -z "$IMAGE_NAME" ]; then
        echo "No jpamb image found. Run 'load' first."
        exit 1
    fi

    echo "Testing Docker image: $IMAGE_NAME"

    echo "Testing Java..."
    $CONTAINER_CMD run --rm "$IMAGE_NAME" java -version

    echo "Testing Maven..."
    $CONTAINER_CMD run --rm "$IMAGE_NAME" mvn --version

    echo "Testing UV..."
    $CONTAINER_CMD run --rm "$IMAGE_NAME" uv --version

    echo "All tests passed!"
}

run_container() {
    IMAGE_NAME=$($CONTAINER_CMD images --format "{{.Repository}}:{{.Tag}}" | grep jpamb | head -1)

    if [ -z "$IMAGE_NAME" ]; then
        echo "No jpamb image found. Run 'load' first."
        exit 1
    fi

    echo "Running Docker container: $IMAGE_NAME"
    echo "Mounting current directory as /workspace"

    $CONTAINER_CMD run -it --rm \
        -v "$(pwd):/workspace" \
        -w /workspace \
        "$IMAGE_NAME" \
        bash
}

export_image() {
    if [ ! -f result ]; then
        echo "No built image found. Run 'build' first."
        exit 1
    fi

    OUTPUT="jpamb-docker-$(date +%Y%m%d).tar.gz"
    echo "Exporting image as $OUTPUT..."

    cp result "$OUTPUT"
    echo "Exported to: $OUTPUT"
    echo "Size: $(du -h "$OUTPUT" | cut -f1)"

    echo ""
    echo "To use this image:"
    echo "  docker load < $OUTPUT"
}

case "${1:-}" in
    build)
        build_image
        ;;
    load)
        load_image
        ;;
    test)
        test_image
        ;;
    run)
        run_container
        ;;
    export)
        export_image
        ;;
    *)
        usage
        exit 1
        ;;
esac