# Define variables
PEM_FILE="/usr/bin/bootloader/FleetManagementWebAppPem.pem"
USER="ubuntu"
HOST="13.58.250.233"
REMOTE_PATH="/home/ubuntu/Fleet_Management/firmware_v*.bin"
DESTINATION="/usr/bin/bootloader"

# Step 1: SSH into the server and immediately exit
ssh -i "$PEM_FILE" "$USER@$HOST" <<EOF
exit
EOF

# Step 2: Copy the file from the server to the target location
scp -i "$PEM_FILE" "$USER@$HOST:$REMOTE_PATH" "$DESTINATION/"

python3 bootloader.py firmware_v*.bin /dev/ttyUSB*