import os
import zipfile
import shutil
from datetime import datetime
from cryptography.fernet import Fernet

class DigitalTimeCapsule:
    def __init__(self):
        self.key = Fernet.generate_key()
        self.cipher_suite = Fernet(self.key)
        self.capsules_dir = "time_capsules"
        
        if not os.path.exists(self.capsules_dir):
            os.makedirs(self.capsules_dir)

    def create_capsule(self, content, unlock_date, title, files=[]):
        """Create an encrypted time capsule with text and optional files."""
        if datetime.strptime(unlock_date, "%d-%m-%Y") <= datetime.now():
            raise ValueError("Unlock date must be in the future!")

        capsule_metadata = {
            "content": content,
            "unlock_date": unlock_date,
            "creation_date": datetime.now().strftime("%d-%m-%Y"),
            "title": title
        }

        # Temporary directory for capsule data
        temp_dir = os.path.join(self.capsules_dir, f"{title}_temp")
        os.makedirs(temp_dir, exist_ok=True)

        # Save metadata to a file
        metadata_file = os.path.join(temp_dir, "metadata.txt")
        with open(metadata_file, "w") as f:
            f.write(str(capsule_metadata))

        # Copy files to the temporary directory
        for file in files:
            file = file.strip().strip('"')  # Remove extra quotes or spaces
            if os.path.exists(file):
                file_name = os.path.basename(file)
                shutil.copy(file, os.path.join(temp_dir, file_name))  # Copy file to temp directory

        # Create a zip archive of the capsule
        zip_filename = os.path.join(self.capsules_dir, f"{title}_{unlock_date}.zip")
        with zipfile.ZipFile(zip_filename, 'w') as zipf:
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    zipf.write(os.path.join(root, file), arcname=file)

        # Encrypt the zip archive
        with open(zip_filename, "rb") as f:
            encrypted_data = self.cipher_suite.encrypt(f.read())

        encrypted_filename = zip_filename.replace(".zip", ".capsule")
        with open(encrypted_filename, "wb") as f:
            f.write(encrypted_data)

        # Cleanup temporary files
        shutil.rmtree(temp_dir)  # Recursively delete the temporary directory
        os.remove(zip_filename)

        return encrypted_filename

    def open_capsule(self, filename):
        """Try to open a time capsule."""
        if not os.path.exists(filename):
            return "Capsule not found!"

        with open(filename, "rb") as f:
            encrypted_data = f.read()

        # Decrypt the content
        zip_data = self.cipher_suite.decrypt(encrypted_data)
        zip_filename = filename.replace(".capsule", "_decrypted.zip")

        # Save the decrypted zip file temporarily
        with open(zip_filename, "wb") as f:
            f.write(zip_data)

        # Extract and check metadata
        with zipfile.ZipFile(zip_filename, 'r') as zipf:
            zipf.extractall(self.capsules_dir)
            metadata_file = os.path.join(self.capsules_dir, "metadata.txt")
            if not os.path.exists(metadata_file):
                return "Invalid capsule format!"

            with open(metadata_file, "r") as f:
                capsule_metadata = eval(f.read())

        # Cleanup decrypted zip file
        os.remove(zip_filename)

        # Check if it's time to open
        if datetime.strptime(capsule_metadata["unlock_date"], "%d-%m-%Y") > datetime.now():
            days_remaining = (datetime.strptime(capsule_metadata["unlock_date"], "%d-%m-%Y") - datetime.now()).days
            return f"This capsule cannot be opened for {days_remaining} more days!"

        # Return content and extracted files location
        content = capsule_metadata["content"]
        extracted_dir = os.path.join(self.capsules_dir, f"{capsule_metadata['title']}_extracted")
        shutil.move(os.path.join(self.capsules_dir, f"{capsule_metadata['title']}_temp"), extracted_dir)

        return f"Content: {content}\nExtracted files are saved in: {extracted_dir}"

def main():
    capsule = DigitalTimeCapsule()
    
    while True:
        print("\n=== Digital Time Capsule ===")
        print("1. Create new time capsule")
        print("2. Open existing capsule")
        print("3. Exit")
        
        choice = input("Choose an option: ")
        
        if choice == "1":
            title = input("Enter capsule title: ")
            content = input("Enter your message: ")
            unlock_date = input("Enter unlock date (DD-MM-YYYY): ")
            file_paths = input("Enter file paths (comma-separated): ").split(',')

            try:
                filename = capsule.create_capsule(content, unlock_date, title, file_paths)
                print(f"Capsule created successfully! Saved as: {filename}")
            except ValueError as e:
                print(f"Error: {e}")
                
        elif choice == "2":
            filename = input("Enter capsule filename: ")
            result = capsule.open_capsule(filename)
            print(f"Result: {result}")
            
        elif choice == "3":
            break

if __name__ == "__main__":
    main()
