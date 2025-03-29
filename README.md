# Bangalore Food Finder

A mobile app that helps you find the best food spots in Bangalore based on your preferences.

## Features

- Find restaurants based on budget
- Filter by number of people
- Specify food type preferences
- Location-based recommendations
- Specific restaurant information

## Development

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/jagadessh20604/bar_food.git
cd bar_food
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up your Together AI API key:
```bash
export TOGETHER_API_KEY=your_api_key_here
```

5. Run the app:
```bash
streamlit run food_app.py
```

### Android Build

The app is automatically built as an Android APK using GitHub Actions. The build process:

1. Sets up the Android SDK and NDK
2. Installs all required dependencies
3. Builds the APK using Buildozer
4. Uploads the APK as an artifact

To get the latest APK:
1. Go to the Actions tab in the repository
2. Click on the latest successful workflow run
3. Download the APK from the artifacts section

## Requirements

- Python 3.9+
- Together AI API key
- Android SDK (for local builds)
- Android NDK (for local builds)

## Build Process

The Android APK is built using the following steps:
1. Clean environment setup
2. Android SDK and NDK installation
3. Buildozer configuration
4. APK compilation
5. Artifact upload

## License

MIT License 