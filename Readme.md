Virtual AI Writer

Virtual AI Writer is an innovative project that uses AI and computer vision technologies to enhance human-computer interaction. It allows users to interact with the system using fingertip detection to perform various tasks such as writing, drawing shapes, erasing content, moving virtual objects, and using a virtual mouse to scroll through PDFs and other applications. The project also includes a webpage for interactive use.

## Features
- **Air Writing**: Write in the air using fingertip gestures, detected by a webcam.
- **Shape Interaction**: Draw, select, and erase shapes in real-time.
- **Virtual Object Manipulation**: Move objects written in the air up and down using gestures.
- **Virtual Mouse**: Scroll through PDFs and interact with the system as a mouse alternative.
- **Webpage Integration**: Access project functionalities through a web-based interface.

## Folder Structure
- **`Virtual-Mouse`**: Contains code and tools for fingertip-based virtual mouse operations.
- **`CvZone-main`**: Main project folder with the core functionality for gesture recognition and virtual interactions.
- **`MARS-Website`**: Webpage folder where users can interact with and use the project's features.
- **`Readme`**: Markdown file with project details.

## Requirements
To use this project, you need to install [OBS Studio](https://obsproject.com/download). Follow these steps to set up the system:
1. Install OBS Studio.
2. Open OBS Studio.
3. Navigate to the `Sources` section.
4. Add a new source, select `Browser`.
5. Paste the following link into the URL field after running the desired folder:
   - For `CvZone-main`, paste: `http://127.0.0.1:5000/video_feed`.
   - Repeat similar steps for other folders, depending on the specific functionality you want to use.

## Getting Started
### Prerequisites
- **Python**: Ensure Python is installed on your system.
- **Libraries**: Install the required libraries using the `requirements.txt` provided in the respective folders.

### Installation
1. Clone this repository:
   ```bash
   git clone https://github.com/vermu490/Virtual-AI-Writer.git
   ```
2. Navigate to the desired folder (e.g., `CvZone-main`).
3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Project
1. Open the terminal and navigate to the folder you want to run (e.g., `CvZone-main`).
2. Run the project:
   ```bash
   python app.py
   ```
3. Open OBS Studio and follow the steps mentioned above to access the live video feed.

## License
Feel free to modify and use it.

## Contributing
Contributions are welcome! If you have ideas or enhancements, feel free to submit a pull request or raise an issue.

---

**Disclaimer**: Ensure that your webcam is properly set up and permissions are granted for the project to function correctly.
