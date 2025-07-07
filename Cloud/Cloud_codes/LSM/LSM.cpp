#include <aws/crt/Api.h>
#include <aws/iot/MqttClient.h>
#include <nlohmann/json.hpp>

#include <iostream>
#include <fstream>
#include <string>
#include <atomic>
#include <chrono>
#include <thread>
#include <ctime>

using json = nlohmann::json;
using namespace Aws::Crt;
using namespace Aws::Iot;

const std::string CAR_ID = "101";

// Callback when a message is published
void onPublish(Mqtt::MqttConnection &connection, uint16_t packetId, int errorCode) {
    if (errorCode) {
        std::cerr << "Error publishing message: " << ErrorDebugString(errorCode) << std::endl;
    } else {
        std::cout << "Message published successfully." << std::endl;
    }
}

// Callback for received messages
void onMessageReceived(Mqtt::MqttConnection &connection, const String &topic, const ByteBuf &payload) {
    std::string message(reinterpret_cast<const char *>(payload.buffer), payload.len);
    json receivedPayload = json::parse(message);

    if (receivedPayload.contains("Car_ID") && receivedPayload["Car_ID"] == CAR_ID) {
        return;
    }
    
    std::cout << "Message received on topic " << topic << ": " << message << std::endl;
}

// Get current timestamp in milliseconds
std::string getCurrentTimestamp() {
    auto now = std::chrono::system_clock::now();
    auto now_ms = std::chrono::duration_cast<std::chrono::milliseconds>(now.time_since_epoch());
    return std::to_string(now_ms.count());
}

int main() {
    // Initialize AWS SDK
    ApiHandle apiHandle;

    // Configure MQTT client
    MqttClient mqttClient;
    MqttClientConnectionConfigBuilder builder("certificate.pem.crt", "private.pem.key");
    builder.WithEndpoint("a32s23mkugyl92-ats.iot.us-east-2.amazonaws.com");
    builder.WithCertificateAuthority("AmazonRootCA1.pem");

    auto config = builder.Build();
    if (!config) {
        std::cerr << "Error creating MQTT config: " << config.LastError() << std::endl;
        return -1;
    }

    auto connection = mqttClient.NewConnection(config);

    if (!connection->Connect(CAR_ID.c_str(), true, 60)) {
        std::cerr << "Error connecting to AWS IoT Core" << std::endl;
        return -1;
    }

    std::cout << "Connected to AWS IoT Core" << std::endl;

    // Subscribe to topic
    auto onSubAck = [](Mqtt::MqttConnection &connection, uint16_t packetId, const String &topic,
                       Mqtt::QOS qos, int errorCode) {
        if (errorCode) {
            std::cerr << "Error subscribing: " << ErrorDebugString(errorCode) << std::endl;
        } else {
            std::cout << "Subscribed to topic: " << topic << std::endl;
        }
    };

    connection->Subscribe("lsm_topic", Mqtt::QOS::AWS_MQTT_QOS_AT_LEAST_ONCE, onMessageReceived, onSubAck);

    // Main loop
    while (true) {
        // Step 1: Read the second line from payload_list.txt
        std::ifstream listFile("../payload_list.txt"); 
        if (!listFile.is_open()) {
            std::cerr << "Failed to open payload_list.txt" << std::endl;
            std::this_thread::sleep_for(std::chrono::seconds(5));
            continue;
        }

        std::string skipLine, jsonPath;
        std::getline(listFile, skipLine);  // Skip the first line
        if (!std::getline(listFile, jsonPath)) {
            std::cerr << "Failed to read second line from payload_list.txt" << std::endl;
            listFile.close();
            std::this_thread::sleep_for(std::chrono::seconds(5));
            continue;
        }
        listFile.close();

        if (jsonPath.empty()) {
            std::cerr << "Second line in payload_list.txt is empty" << std::endl;
            std::this_thread::sleep_for(std::chrono::seconds(5));
            continue;
        }

        // Step 2: Read JSON from the specified path
        std::ifstream inputFile(jsonPath);
        if (!inputFile.is_open()) {
            std::cerr << "Failed to open JSON file: " << jsonPath << std::endl;
            std::this_thread::sleep_for(std::chrono::seconds(5));
            continue;
        }

        json payload;
        try {
            inputFile >> payload;
        } catch (const std::exception &e) {
            std::cerr << "Error parsing JSON file: " << e.what() << std::endl;
            inputFile.close();
            std::this_thread::sleep_for(std::chrono::seconds(5));
            continue;
        }
        inputFile.close();

        // Step 3: Add dynamic timestamp
        payload["time"] = getCurrentTimestamp();

        std::string message = payload.dump();
        ByteBuf payloadBuf = ByteBufFromArray((const uint8_t *)message.data(), message.size());

        // Step 4: Publish the message
        connection->Publish(
            "lsm_topic",
            Mqtt::QOS::AWS_MQTT_QOS_AT_LEAST_ONCE,
            false,
            payloadBuf,
            onPublish
        );

        std::this_thread::sleep_for(std::chrono::seconds(5));
    }

    return 0;
}
