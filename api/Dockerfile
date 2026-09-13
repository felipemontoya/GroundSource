# The GroundSource backend image.
#
# Lives next to the code it builds so that `../dev/` and `../ops/` can both
# reference one definition (see ../AGENTS.md). Single stage: every runtime
# dependency ships as a wheel, so there is no build toolchain to discard.

FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_ROOT_USER_ACTION=ignore

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-compile -r requirements.txt

COPY . ./

# Run unprivileged. The source tree is bind-mounted read-only in dev, and
# PYTHONDONTWRITEBYTECODE keeps the container from trying to write into it.
RUN useradd --system --create-home --home-dir /home/app --shell /usr/sbin/nologin app
USER app

EXPOSE 8000

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["uvicorn", "groundsource.asgi:application", "--host", "0.0.0.0", "--port", "8000"]
