# moral_annotation_tool

## Run a MongoDB Instance
1. Install MongoDB ([Tutorial](https://docs.mongodb.com/getting-started/shell/installation/)). If you don't want to install MongoDB system wide, just unpack the tarball to `path/to/mongodb`.
2. Create a writable empty directory `path/to/db`
3. Run `mongod --dbpath path/to/db --port 8888` in the background (or `/path/to/mongodb/bin/mongod --dbpath path/to/db --port 8888` if MongoDB is not installed system wide).

## Run the Annotation Tool
1. Enter the project directory.
2. Run `python moral_annotation_tool.py`.
3. Open `0.0.0.0:8080` in the browser.

## Dependency
* Python3 is required.
* `pip install flask passlib pymongo`
