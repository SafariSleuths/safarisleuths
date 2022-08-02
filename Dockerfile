FROM node:16.13 as ui
WORKDIR /wrk/
COPY ui/package.json package.json
COPY ui/package-lock.json package-lock.json
COPY ui/tsconfig.json tsconfig.json
RUN npm install

COPY ui/src src
COPY ui/public public
RUN npm run build

FROM python:3.10
WORKDIR /wrk/

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY --from=ui /wrk/build ./ui/build
COPY app.py app.py
COPY api api
CMD ["python", "app.py"]
