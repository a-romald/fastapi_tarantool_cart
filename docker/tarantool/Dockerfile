FROM tarantool/tarantool:3.2.0

# Install dependencies
RUN apt-get update && \
    apt-get install -y git unzip cmake tt

# Initialize tt structure
RUN tt init && \
    tt rocks install expirationd

# Config catalog
ADD config/tarantool /opt/tarantool
CMD ["tarantool", "/opt/tarantool/app.lua"]
