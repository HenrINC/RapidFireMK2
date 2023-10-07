# PS3 Trophy Toolset Docker Image

This Docker image contains the PS3 Trophy Toolset and can be used to add trophies to your PS3 games.

## Building the Image

To build the Docker image, run the following command in the root directory of the project:

```
docker build -t ps3-trophy-toolset .
```

This will build the Docker image and tag it as `ps3-trophy-toolset`.

## Running the Image

To run the Docker image, you need to provide at least the following environment variables:

- `PS3_HOST`: The IP address of your PS3.

You can run the Docker image using the following command:

```
docker run --rm -e PS3_HOST=your.ps3.ip.address -v /path/to/trophies:/trophies ps3-trophy-toolset 
```

You can modify the environment variables and the command to match your specific use case.

