# Vitox Creator Studio - Pro
The ultimate video platform ecosystem. Features a web-based Creator Studio and a Flutter mobile application.

## 🚀 Web Architecture
- **Backend**: Flask (Python) with PostgreSQL.
- **Frontend**: Vanilla HTML5, CSS3 (Premium Glassmorphism), JavaScript.
- **AI Integration**: OpenRouter (Llama 3) & Google Gemini.
- **Storage**: Cloudinary for high-speed video delivery.

## 📱 Vitox Mobile (Flutter App)
A professional Flutter application source is provided in the `/mobile_app` folder. It is designed to connect directly to the Vitox Web Backend.

### How to Run:
1. **Install Flutter**: Make sure you have the [Flutter SDK](https://docs.flutter.dev/get-started/install) installed.
2. **Setup URL**: Open `mobile_app/lib/main.dart` and update the `baseUrl` with your Render/Live URL.
3. **Navigate**: `cd mobile_app`
4. **Get Packages**: `flutter pub get`
5. **Run**:
   - For Android: `flutter run`
   - For iOS: `flutter run` (Requires macOS & Xcode)

### Features:
- **Premium UI**: Dark mode with Outfit typography.
- **Live Feed**: Fetches videos directly from the web server.
- **V-Snaps**: Vertical scroll interface for short videos, synced with the backend.
- **Studio Hub**: Mobile dashboard for channel management.

## 🛠 Tech Stack
- **Database**: PostgreSQL (Render) / SQLite (Local).
- **APIs**: RESTful endpoints in `server.py`.
- **Styling**: Modern CSS with CSS Variables and Animations.
