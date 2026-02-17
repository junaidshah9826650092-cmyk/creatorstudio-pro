import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:video_player/video_player.dart';
import 'package:cached_network_image/cached_network_image.dart';

// CHANGE THIS TO YOUR RENDER URL
const String baseUrl = 'https://creatorstudio-pro.onrender.com'; 

void main() {
  runApp(const VitoxApp());
}

class VitoxApp extends StatelessWidget {
  const VitoxApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Vitox Platform',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: const Color(0xFF0F0F0F),
        primaryColor: const Color(0xFFFF0055),
        textTheme: GoogleFonts.outfitTextTheme(ThemeData.dark().textTheme),
        colorScheme: const ColorScheme.dark(
          primary: Color(0xFFFF0055),
          secondary: Color(0xFFFF5500),
        ),
      ),
      home: const MainScreen(),
    );
  }
}

class MainScreen extends StatefulWidget {
  const MainScreen({super.key});

  @override
  State<MainScreen> createState() => _MainScreenState();
}

class _MainScreenState extends State<MainScreen> {
  int _selectedIndex = 0;

  final List<Widget> _pages = [
    const FeedScreen(),
    const SnapsScreen(),
    const DashboardScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _pages[_selectedIndex],
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _selectedIndex,
        onTap: (index) => setState(() => _selectedIndex = index),
        backgroundColor: const Color(0xFF0F0F0F),
        selectedItemColor: const Color(0xFFFF0055),
        unselectedItemColor: Colors.white54,
        showSelectedLabels: true,
        showUnselectedLabels: true,
        type: BottomNavigationBarType.fixed,
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.home_filled), label: 'Feed'),
          BottomNavigationBarItem(icon: Icon(Icons.play_circle_fill), label: 'Snaps'),
          BottomNavigationBarItem(icon: Icon(Icons.dashboard_rounded), label: 'Studio'),
        ],
      ),
    );
  }
}

// --- Video Model ---
class VitoxVideo {
  final String id;
  final String title;
  final String url;
  final String user;
  final int views;
  final String timestamp;

  VitoxVideo({required this.id, required this.title, required this.url, required this.user, required this.views, required this.timestamp});

  factory VitoxVideo.fromJson(Map<String, dynamic> json) {
    return VitoxVideo(
      id: json['id'].toString(),
      title: json['title'] ?? 'Vitox Masterpiece',
      url: json['video_url'] ?? '',
      user: (json['user_email'] ?? 'Official').split('@')[0],
      views: json['views'] ?? 0,
      timestamp: json['timestamp'] ?? '',
    );
  }
}

// --- Feed Screen ---
class FeedScreen extends StatefulWidget {
  const FeedScreen({super.key});

  @override
  State<FeedScreen> createState() => _FeedScreenState();
}

class _FeedScreenState extends State<FeedScreen> {
  List<VitoxVideo> videos = [];
  bool isLoading = true;

  @override
  void initState() {
    super.initState();
    fetchVideos();
  }

  Future<void> fetchVideos() async {
    try {
      final res = await http.get(Uri.parse('$baseUrl/api/videos?type=video'));
      if (res.statusCode == 200) {
        final List data = json.decode(res.body);
        setState(() {
          videos = data.map((v) => VitoxVideo.fromJson(v)).toList();
          isLoading = false;
        });
      }
    } catch (e) {
      print("Error: $e");
      setState(() => isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            const Icon(Icons.v_stable, color: Color(0xFFFF0055), size: 30),
            const SizedBox(width: 8),
            Text('Vitox', style: GoogleFonts.outfit(fontWeight: FontWeight.w800, fontSize: 24)),
          ],
        ),
        actions: [
          IconButton(icon: const Icon(Icons.search), onPressed: () {}),
          const Padding(
            padding: EdgeInsets.symmetric(horizontal: 12),
            child: CircleAvatar(backgroundColor: Colors.blueGrey, child: Text('J', style: TextStyle(color: Colors.white))),
          ),
        ],
        backgroundColor: const Color(0xFF0F0F0F),
        elevation: 0,
      ),
      body: isLoading 
        ? const Center(child: CircularProgressIndicator(color: Color(0xFFFF0055)))
        : RefreshIndicator(
            onRefresh: fetchVideos,
            child: ListView.builder(
              itemCount: videos.length,
              itemBuilder: (context, index) => VideoCard(video: videos[index]),
            ),
          ),
    );
  }
}

class VideoCard extends StatelessWidget {
  final VitoxVideo video;
  const VideoCard({super.key, required this.video});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        AspectRatio(
          aspectRatio: 16 / 9,
          child: Container(
            color: Colors.white10,
            child: const Center(child: Icon(Icons.play_arrow, size: 50, color: Colors.white)),
          ),
        ),
        Padding(
          padding: const EdgeInsets.all(12),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const CircleAvatar(backgroundColor: Color(0xFFFF0055), radius: 20, child: Icon(Icons.person, color: Colors.white, size: 20)),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      video.title,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: GoogleFonts.outfit(fontSize: 16, fontWeight: FontWeight.w500),
                    ),
                    const SizedBox(height: 4),
                    Text('${video.user} • ${video.views} views • Just now', style: const TextStyle(color: Colors.white54, fontSize: 13)),
                  ],
                ),
              ),
              IconButton(icon: const Icon(Icons.more_vert, size: 20), onPressed: () {}),
            ],
          ),
        ),
      ],
    );
  }
}

// --- V-Snaps (Shorts) ---
class SnapsScreen extends StatefulWidget {
  const SnapsScreen({super.key});

  @override
  State<SnapsScreen> createState() => _SnapsScreenState();
}

class _SnapsScreenState extends State<SnapsScreen> {
  List<VitoxVideo> snaps = [];
  bool isLoading = true;

  @override
  void initState() {
    super.initState();
    fetchSnaps();
  }

  Future<void> fetchSnaps() async {
    try {
      final res = await http.get(Uri.parse('$baseUrl/api/videos?type=short'));
      if (res.statusCode == 200) {
        final List data = json.decode(res.body);
        setState(() {
          snaps = data.map((v) => VitoxVideo.fromJson(v)).toList();
          isLoading = false;
        });
      }
    } catch (e) {
      setState(() => isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (isLoading) return const Center(child: CircularProgressIndicator(color: Color(0xFFFF0055)));
    
    return PageView.builder(
      scrollDirection: Axis.vertical,
      itemCount: snaps.length,
      itemBuilder: (context, index) {
        final snap = snaps[index];
        return Stack(
          fit: StackFit.expand,
          children: [
            Container(color: Colors.black),
            const Center(child: Icon(Icons.play_circle_outline, color: Colors.white24, size: 80)),
            Positioned(
              right: 12,
              bottom: 80,
              child: Column(
                children: const [
                  SnapAction(icon: Icons.favorite, label: 'Like'),
                  SnapAction(icon: Icons.comment, label: 'Chat'),
                  SnapAction(icon: Icons.share, label: 'Share'),
                ],
              ),
            ),
            Positioned(
              left: 16,
              bottom: 20,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const CircleAvatar(radius: 18, backgroundColor: Colors.white),
                      const SizedBox(width: 10),
                      Text('@${snap.user}', style: GoogleFonts.outfit(fontWeight: FontWeight.w700)),
                      const SizedBox(width: 10),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                        decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(20)),
                        child: const Text('Follow', style: TextStyle(color: Colors.black, fontSize: 12, fontWeight: FontWeight.w800)),
                      )
                    ],
                  ),
                  const SizedBox(height: 10),
                  Text(snap.title, style: const TextStyle(color: Colors.white, fontSize: 14)),
                ],
              ),
            )
          ],
        );
      },
    );
  }
}

class SnapAction extends StatelessWidget {
  final IconData icon;
  final String label;
  const SnapAction({super.key, required this.icon, required this.label});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 12),
      child: Column(
        children: [
          Icon(icon, color: Colors.white, size: 32),
          const SizedBox(height: 4),
          Text(label, style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }
}

// --- Dashboard Screen ---
class DashboardScreen extends StatelessWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.auto_awesome_motion, size: 80, color: Color(0xFFFF0055)),
            const SizedBox(height: 20),
            Text('Vitox Studio Mobile', style: GoogleFonts.outfit(fontSize: 28, fontWeight: FontWeight.w800)),
            const SizedBox(height: 10),
            const Text('Manage your channel on the go.', textAlign: TextAlign.center, style: TextStyle(color: Colors.white54)),
            const SizedBox(height: 30),
            ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFFFF0055),
                minimumSize: const Size(double.infinity, 50),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
              onPressed: () {},
              child: const Text('GO TO ANALYTICS', style: TextStyle(fontWeight: FontWeight.w800)),
            ),
          ],
        ),
      ),
    );
  }
}
