# build stage
FROM maven:3.9-amazoncorretto-21 AS build
WORKDIR /app
COPY . .
RUN mvn clean install -DskipTests=true

# run stage
FROM amazoncorretto:21
COPY --from=build /app/target/camara-api-gateway-0.0.1.jar ./app.jar
CMD ["java", "-jar", "./app.jar"]