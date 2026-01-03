FROM python:3.10-slim-bullseye

# تحديث وتثبيت الأدوات اللازمة
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/

COPY requirements.txt .

# هنا التعديل: بنثبت المتطلبات، وبعدها بنجبره يرجع النسخ القديمة الشغالة
RUN python3 -m pip install --upgrade pip setuptools \
    && pip3 install --no-cache-dir --upgrade --requirement requirements.txt \
    && pip3 install --force-reinstall pyrogram==2.0.106 py-tgcalls==0.9.9

COPY . .

CMD ["python3", "-m", "BrandrdXMusic"]
