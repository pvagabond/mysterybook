# Use an official Python runtime as a base image
FROM python:3.6-windowsservercore-ltsc2016

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
ADD . /app

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt
RUN python manage.py migrate
RUN python manage.py collectstatic --noinput
#RUN python manage.py shell -c "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@example.com', 'adminpass')"

# Make port 80 available to the world outside this container
EXPOSE 80

# Define environment variable
ENV NAME World

   
# Run app.py when the container launches
CMD ["python", "manage.py", "runserver", "0.0.0.0:80"]