FROM ubuntu:24.04

ENV C_INCLUDE_PATH=/usr/lib/llvm-18/lib/clang/18/include:/usr/include:/usr/lib/gcc/x86_64-linux-gnu/13/include/:/usr/include/linux/

ENV CPLUS_INCLUDE_PATH=/usr/lib/llvm-18/lib/clang/18/include:/usr/include/c++/13:/usr/include:/usr/lib/gcc/x86_64-linux-gnu/13/include/:/usr/include/linux/

RUN apt-get update && apt-get install -y \
    gh \
    jq \
    git \
    python3-requests \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY ./ghscript.py .

CMD [ "python3", "./ghscript.py" ]