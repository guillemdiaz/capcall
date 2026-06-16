# Pull base image
FROM node:20-alpine

# Set work directory
WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Copy project
COPY . .

# Expose the Vite port
EXPOSE 5173

# Command to start the development server
CMD ["npm", "run", "dev"]