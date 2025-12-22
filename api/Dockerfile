# Use miniconda3 as base image to handle geospatial dependencies (GDAL, Rasterio, etc.)
FROM continuumio/miniconda3

# Set working directory
WORKDIR /app

# Copy environment configuration
COPY environment.yml .

# Create conda environment
RUN conda env create -f environment.yml && conda clean -afy

# Copy the application code
COPY . .

# Expose the port
EXPOSE 25376

# Run the application
# Using "conda run" ensures the correct environment is active
CMD ["conda", "run", "--no-capture-output", "-n", "demo_scensUI_3_api", "python", "main.py"]
