# Imagem de desenvolvimento do front (issue #10): `next dev` com o código montado
# pelo compose. A imagem de produção fica para o deploy (Sprint 3, Vercel).
FROM node:24-alpine

ENV NEXT_TELEMETRY_DISABLED=1

WORKDIR /app
# Roda como o usuário `node` (sem root). As pastas são criadas aqui para os volumes
# anônimos do compose (node_modules e .next) nascerem com o dono certo.
RUN chown node:node /app
USER node
RUN mkdir .next

# Só os manifestos primeiro: o npm ci fica em cache até o package-lock.json mudar.
COPY --chown=node:node package.json package-lock.json ./
RUN npm ci

COPY --chown=node:node . .

EXPOSE 3000
CMD ["npm", "run", "dev", "--", "--hostname", "0.0.0.0"]
