# Bangalore Food Finder App

A mobile app that helps you find the best food options in Bangalore based on your preferences, budget, and location.

## Features

- Search for food options based on:
  - Budget
  - Number of people
  - Food type
  - Location (optional)
  - Specific restaurant (optional)
- AI-powered recommendations
- Mobile-friendly interface
- Offline support

## Installation

### For Users
1. Download the latest APK from the [Releases](https://github.com/YOUR_USERNAME/bangalore-food-finder/releases) page
2. Install the APK on your Android device
3. Launch the app and start finding food!

### For Developers
1. Clone the repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/bangalore-food-finder.git
   cd bangalore-food-finder
   ```

2. Create a virtual environment and activate it:
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
   export TOGETHER_API_KEY="your_api_key_here"
   ```

5. Run the app locally:
   ```bash
   python food_android.py
   ```

## Building the APK

The APK is automatically built using GitHub Actions when you push to the main branch. You can find the latest APK in the [Actions](https://github.com/YOUR_USERNAME/bangalore-food-finder/actions) tab.

To build locally:
```bash
buildozer android debug
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 