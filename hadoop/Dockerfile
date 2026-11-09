# ---------- A1: imagen Hadoop (standalone) + Python 3 + OpenSSH ----------
FROM debian:bookworm-slim

ARG HADOOP_VERSION=3.3.6
ARG HADOOP_UID=1000

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    PYTHONIOENCODING=utf-8

# Java (OpenJDK 17), Python 3 y OpenSSH (servidor + cliente)
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      openjdk-17-jre-headless python3 openssh-server openssh-client \
      curl ca-certificates procps time \
 && ln -s /usr/lib/jvm/java-17-openjdk-"$(dpkg --print-architecture)" /usr/lib/jvm/java-17-openjdk \
 && rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk \
    HADOOP_HOME=/opt/hadoop
ENV HADOOP_CONF_DIR=${HADOOP_HOME}/etc/hadoop \
    PATH=${PATH}:/opt/hadoop/bin:/opt/hadoop/sbin

# Hadoop: usa hadoop/cache/hadoop-<ver>.tar.gz si existe (build rapido/offline); si no, lo descarga.
# En ambos casos se verifica el SHA-512 oficial (modo standalone: no requiere configuracion).
RUN --mount=type=bind,source=cache,target=/tmp/cache \
    set -eux; \
    URL=https://archive.apache.org/dist/hadoop/common/hadoop-${HADOOP_VERSION}/hadoop-${HADOOP_VERSION}.tar.gz; \
    if [ -f /tmp/cache/hadoop-${HADOOP_VERSION}.tar.gz ]; then cp /tmp/cache/hadoop-${HADOOP_VERSION}.tar.gz /tmp/hadoop.tgz; \
    else curl -fsSL -o /tmp/hadoop.tgz "$URL"; fi; \
    curl -fsSL -o /tmp/hadoop.sha "$URL.sha512"; \
    echo "$(awk '{print $NF}' /tmp/hadoop.sha)  /tmp/hadoop.tgz" | sha512sum -c -; \
    mkdir -p ${HADOOP_HOME}; \
    tar -xzf /tmp/hadoop.tgz -C ${HADOOP_HOME} --strip-components=1; \
    rm -rf /tmp/hadoop.tgz /tmp/hadoop.sha ${HADOOP_HOME}/share/doc; \
    echo "export JAVA_HOME=${JAVA_HOME}" >> ${HADOOP_HOME}/etc/hadoop/hadoop-env.sh

# Las sesiones SSH no heredan los ENV de Docker: se publican via PAM (/etc/environment)
RUN { echo "JAVA_HOME=${JAVA_HOME}"; echo "HADOOP_HOME=${HADOOP_HOME}"; \
      echo "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${HADOOP_HOME}/bin:${HADOOP_HOME}/sbin"; \
      echo "LANG=C.UTF-8"; } > /etc/environment

# Usuario sin contrasena ('*' = sin password valido pero cuenta NO bloqueada, asi sshd acepta llaves)
RUN useradd -m -u ${HADOOP_UID} -s /bin/bash hadoop \
 && usermod -p '*' hadoop \
 && mkdir -p /run/sshd /data/input /data/output /keys /opt/mapreduce \
 && chown hadoop:hadoop /data/output /keys

# sshd: solo llaves, sin root, solo el usuario hadoop
RUN printf '%s\n' \
      'PasswordAuthentication no' \
      'KbdInteractiveAuthentication no' \
      'PermitRootLogin no' \
      'PubkeyAuthentication yes' \
      'AllowUsers hadoop' \
    > /etc/ssh/sshd_config.d/hadoop.conf

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

WORKDIR /opt/mapreduce
EXPOSE 22
ENTRYPOINT ["/entrypoint.sh"]
CMD ["/usr/sbin/sshd", "-D", "-e"]
