import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter_staggered_animations/flutter_staggered_animations.dart';

// --- CONFIGURATION ---
// ⚠️ AI POLICY: All uploads are scanned via Gemini AI for 18+ and harmful content.
const String baseUrl =
    'https://creatorstudio-pro.onrender.com'; // Update with your live URL

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
        canvasColor: const Color(0xFF0F0F0F),
        textTheme: GoogleFonts.outfitTextTheme(ThemeData.dark().textTheme),
        colorScheme: const ColorScheme.dark(
          primary: Color(0xFFFF0055),
          secondary: Color(0xFFFF5500),
          surface: Color(0xFF1E1E1E),
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
    const CreateScreen(),
    const SquadScreen(),
    const LibraryScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _pages[_selectedIndex],
      bottomNavigationBar: Container(
        decoration: const BoxDecoration(
          border: Border(top: BorderSide(color: Colors.white10, width: 0.5)),
        ),
        child: BottomNavigationBar(
          currentIndex: _selectedIndex,
          onTap: (index) {
            if (index == 2) {
              _showCreateModal(context);
            } else {
              setState(() => _selectedIndex = index);
            }
          },
          backgroundColor: const Color(0xFF0F0F0F),
          selectedItemColor: Colors.white,
          unselectedItemColor: Colors.white54,
          selectedLabelStyle:
              const TextStyle(fontSize: 10, fontWeight: FontWeight.w600),
          unselectedLabelStyle: const TextStyle(fontSize: 10),
          type: BottomNavigationBarType.fixed,
          items: const [
            BottomNavigationBarItem(
                icon: Icon(Icons.home_filled),
                activeIcon: Icon(Icons.home),
                label: 'Home'),
            BottomNavigationBarItem(
                icon: Icon(Icons.play_circle_outline),
                activeIcon: Icon(Icons.play_circle_fill),
                label: 'Snaps'),
            BottomNavigationBarItem(
                icon: Icon(Icons.add_circle_outline,
                    size: 40, color: Colors.white),
                label: ''),
            BottomNavigationBarItem(
                icon: Icon(Icons.subscriptions_outlined),
                activeIcon: Icon(Icons.subscriptions),
                label: 'Squad'),
            BottomNavigationBarItem(
                icon: Icon(Icons.video_library_outlined),
                activeIcon: Icon(Icons.video_library),
                label: 'Library'),
          ],
        ),
      ),
    );
  }

  void _showCreateModal(BuildContext context) {
    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF1E1E1E),
      shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (context) => Container(
        padding: const EdgeInsets.symmetric(vertical: 20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                    color: Colors.white24,
                    borderRadius: BorderRadius.circular(2))),
            const SizedBox(height: 20),
            _createItem(Icons.upload, 'Upload a video'),
            _createItem(Icons.bolt, 'Create a Snap'),
            _createItem(Icons.sensors, 'Go live'),
            _createItem(Icons.edit_note, 'Create a post'),
          ],
        ),
      ),
    );
  }

  Widget _createItem(IconData icon, String title) {
    return ListTile(
      leading: CircleAvatar(
          backgroundColor: Colors.white10,
          child: Icon(icon, color: Colors.white)),
      title: Text(title, style: const TextStyle(fontWeight: FontWeight.w600)),
      onTap: () => Navigator.pop(context),
    );
  }
}

class VitoxVideo {
  final String id;
  final String title;
  final String thumbnailUrl;
  final String videoUrl;
  final String user;
  final int views;
  final String timestamp;
  final int likes;

  VitoxVideo(
      {required this.id,
      required this.title,
      required this.thumbnailUrl,
      required this.videoUrl,
      required this.user,
      required this.views,
      required this.timestamp,
      required this.likes});

  factory VitoxVideo.fromJson(Map<String, dynamic> json) {
    String vUrl = json['video_url'] ?? '';
    return VitoxVideo(
      id: json['id'].toString(),
      title: json['title'] ?? 'Vitox Masterpiece',
      thumbnailUrl: vUrl.replaceAll('.mp4', '.jpg').replaceAll('.mov', '.jpg'),
      videoUrl: vUrl,
      user: (json['user_email'] ?? 'Official Creator').split('@')[0],
      views: json['views'] ?? 0,
      timestamp: json['timestamp'] ?? 'Just now',
      likes: json['likes'] ?? 0,
    );
  }
}

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
            Text('Vitox',
                style: GoogleFonts.outfit(
                    fontWeight: FontWeight.w900,
                    fontSize: 24,
                    letterSpacing: -1)),
          ],
        ),
        actions: [
          IconButton(icon: const Icon(Icons.cast), onPressed: () {}),
          IconButton(
              icon: const Icon(Icons.notifications_none), onPressed: () {}),
          IconButton(icon: const Icon(Icons.search), onPressed: () {}),
          const Padding(
            padding: EdgeInsets.only(right: 12, left: 4),
            child: CircleAvatar(
                radius: 14,
                backgroundColor: Colors.blueGrey,
                child: Text('J',
                    style: TextStyle(fontSize: 12, color: Colors.white))),
          ),
        ],
        backgroundColor: const Color(0xFF0F0F0F),
        elevation: 0,
      ),
      body: Column(
        children: [
          _buildCategories(),
          Expanded(
            child: isLoading
                ? const Center(
                    child: CircularProgressIndicator(color: Color(0xFFFF0055)))
                : RefreshIndicator(
                    onRefresh: fetchVideos,
                    child: AnimationLimiter(
                      child: ListView.builder(
                        itemCount: videos.length,
                        itemBuilder: (context, index) =>
                            AnimationConfiguration.staggeredList(
                          position: index,
                          duration: const Duration(milliseconds: 500),
                          child: SlideAnimation(
                            verticalOffset: 50.0,
                            child: FadeInAnimation(
                                child: VideoCard(video: videos[index])),
                          ),
                        ),
                      ),
                    ),
                  ),
          ),
        ],
      ),
    );
  }

  Widget _buildCategories() {
    final chips = [
      'All',
      'Gaming',
      'Music',
      'Live',
      'Tech',
      'Education',
      'Comedy'
    ];
    return Container(
      height: 50,
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: ListView.builder(
        scrollDirection: Axis.horizontal,
        itemCount: chips.length,
        padding: const EdgeInsets.symmetric(horizontal: 12),
        itemBuilder: (context, index) => Padding(
          padding: const EdgeInsets.only(right: 8),
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            decoration: BoxDecoration(
              color: index == 0 ? Colors.white : Colors.white10,
              borderRadius: BorderRadius.circular(8),
            ),
            alignment: Alignment.center,
            child: Text(chips[index],
                style: TextStyle(
                    color: index == 0 ? Colors.black : Colors.white,
                    fontWeight: FontWeight.bold,
                    fontSize: 13)),
          ),
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
        Stack(
          children: [
            AspectRatio(
              aspectRatio: 16 / 9,
              child: CachedNetworkImage(
                imageUrl: video.thumbnailUrl,
                placeholder: (context, url) => Container(color: Colors.white10),
                errorWidget: (context, url, error) => Container(
                    color: Colors.black,
                    child: const Icon(Icons.video_library_outlined,
                        color: Colors.white24)),
                fit: BoxFit.cover,
              ),
            ),
            Positioned(
              bottom: 8,
              right: 8,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                    color: Colors.black87,
                    borderRadius: BorderRadius.circular(4)),
                child: const Text('10:05',
                    style:
                        TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
              ),
            )
          ],
        ),
        Padding(
          padding: const EdgeInsets.fromLTRB(12, 12, 12, 24),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const CircleAvatar(
                  radius: 18,
                  backgroundColor: Color(0xFFFF0055),
                  child: Icon(Icons.person, color: Colors.white, size: 20)),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(video.title,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                            fontSize: 15, fontWeight: FontWeight.w600)),
                    const SizedBox(height: 4),
                    Text(
                        '${video.user} • ${video.views} views • ${video.timestamp}',
                        style: const TextStyle(
                            color: Colors.white54, fontSize: 12)),
                  ],
                ),
              ),
              const Icon(Icons.more_vert, size: 20, color: Colors.white),
            ],
          ),
        ),
      ],
    );
  }
}

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
    if (isLoading)
      return const Center(
          child: CircularProgressIndicator(color: Color(0xFFFF0055)));

    return Scaffold(
      backgroundColor: Colors.black,
      body: PageView.builder(
        scrollDirection: Axis.vertical,
        itemCount: snaps.length,
        itemBuilder: (context, index) {
          final snap = snaps[index];
          return Stack(
            fit: StackFit.expand,
            children: [
              const Center(
                  child: Icon(Icons.play_circle_outline,
                      color: Colors.white24, size: 100)),
              Container(
                decoration: const BoxDecoration(
                  gradient: LinearGradient(
                      begin: Alignment.topCenter,
                      end: Alignment.bottomCenter,
                      colors: [
                        Colors.black38,
                        Colors.transparent,
                        Colors.transparent,
                        Colors.black87
                      ]),
                ),
              ),
              Positioned(
                right: 12,
                bottom: 100,
                child: Column(
                  children: [
                    SnapAction(
                        icon: Icons.favorite,
                        label: snap.likes > 0 ? snap.likes.toString() : 'Like'),
                    SnapAction(icon: Icons.comment, label: 'Chat'),
                    SnapAction(icon: Icons.share, label: 'Share'),
                    SnapAction(icon: Icons.loop, label: 'Remix'),
                    const CircleAvatar(
                        radius: 20,
                        backgroundColor: Colors.white10,
                        child: Icon(Icons.music_note,
                            color: Colors.white, size: 20)),
                  ],
                ),
              ),
              Positioned(
                left: 16,
                bottom: 30,
                right: 80,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        CircleAvatar(
                            radius: 18,
                            backgroundColor: const Color(0xFFFF0055),
                            child: Text(snap.user[0].toUpperCase())),
                        const SizedBox(width: 10),
                        Text('@${snap.user}',
                            style: const TextStyle(
                                fontWeight: FontWeight.bold, fontSize: 16)),
                        const SizedBox(width: 12),
                        Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 14, vertical: 6),
                          decoration: BoxDecoration(
                              color: const Color(0xFFFF0055),
                              borderRadius: BorderRadius.circular(20)),
                          child: const Text('Squad',
                              style: TextStyle(
                                  color: Colors.white,
                                  fontSize: 12,
                                  fontWeight: FontWeight.w800)),
                        )
                      ],
                    ),
                    const SizedBox(height: 12),
                    Text(snap.title,
                        style: const TextStyle(
                            color: Colors.white,
                            fontSize: 15,
                            fontWeight: FontWeight.w500)),
                    const SizedBox(height: 8),
                    Row(
                      children: const [
                        Icon(Icons.music_note, size: 14, color: Colors.white70),
                        SizedBox(width: 8),
                        Text('Original Sound - Vitox Audio',
                            style:
                                TextStyle(color: Colors.white70, fontSize: 13)),
                      ],
                    ),
                  ],
                ),
              )
            ],
          );
        },
      ),
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
      padding: const EdgeInsets.symmetric(vertical: 14),
      child: Column(
        children: [
          Icon(icon,
              color: Colors.white,
              size: 34,
              shadows: const [Shadow(blurRadius: 10, color: Colors.black45)]),
          const SizedBox(height: 6),
          Text(label,
              style: const TextStyle(
                  color: Colors.white,
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
                  shadows: [Shadow(blurRadius: 5, color: Colors.black)])),
        ],
      ),
    );
  }
}

class SquadScreen extends StatelessWidget {
  const SquadScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
          title: const Text('Squad Feed'),
          backgroundColor: const Color(0xFF0F0F0F),
          elevation: 0),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.group_work, size: 80, color: Colors.white10),
            const SizedBox(height: 20),
            const Text('Join a Creator Squad',
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
            const SizedBox(height: 10),
            const Text('Their latest videos will appear here.',
                style: TextStyle(color: Colors.white54)),
          ],
        ),
      ),
    );
  }
}

class LibraryScreen extends StatefulWidget {
  const LibraryScreen({super.key});

  @override
  State<LibraryScreen> createState() => _LibraryScreenState();
}

class _LibraryScreenState extends State<LibraryScreen> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
          title: const Text('Library'),
          backgroundColor: const Color(0xFF0F0F0F),
          elevation: 0),
      body: ListView(
        children: [
          const SizedBox(height: 10),
          _libItem(Icons.history, 'History'),
          _libItem(Icons.playlist_play, 'Playlists'),
          _libItem(Icons.thumb_up_alt_outlined, 'Liked videos'),
          _libItem(Icons.cloud_download_outlined, 'Downloads'),
          const Divider(color: Colors.white10, height: 40),
          const Padding(
            padding: EdgeInsets.symmetric(horizontal: 24, vertical: 10),
            child: Text('STUDIO ANALYTICS',
                style: TextStyle(
                    color: Colors.white38,
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                    letterSpacing: 1.5)),
          ),
          _studioCard(),
          const SizedBox(height: 20),
          _aiChatBubble(),
        ],
      ),
    );
  }

  Widget _libItem(IconData icon, String title) {
    return ListTile(
      leading: Icon(icon, color: Colors.white),
      title: Text(title, style: const TextStyle(fontWeight: FontWeight.w500)),
      trailing:
          const Icon(Icons.chevron_right, size: 18, color: Colors.white24),
    );
  }

  Widget _studioCard() {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
          color: const Color(0xFF1E1E1E),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: Colors.white10)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const CircleAvatar(
                  radius: 25,
                  backgroundColor: Color(0xFFFF0055),
                  child: Icon(Icons.analytics, color: Colors.white)),
              const SizedBox(width: 15),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: const [
                  Text('Junaid Shah',
                      style:
                          TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                  Text('Official Creator Studio',
                      style: TextStyle(color: Colors.white54, fontSize: 13)),
                ],
              )
            ],
          ),
          const SizedBox(height: 25),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              _stat('1.2M', 'Views'),
              _stat('45K', 'Squad'),
              _stat('₹12,400', 'Earned'),
            ],
          )
        ],
      ),
    );
  }

  Widget _stat(String val, String label) {
    return Column(
      children: [
        Text(val,
            style: const TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w900,
                color: Color(0xFFFF0055))),
        const SizedBox(height: 4),
        Text(label,
            style: const TextStyle(
                fontSize: 11,
                color: Colors.white38,
                fontWeight: FontWeight.bold)),
      ],
    );
  }

  Widget _aiChatBubble() {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
            colors: [Color(0xFFff0055), Color(0xFFff5500)]),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: const [
              Icon(Icons.auto_awesome, color: Colors.white, size: 20),
              SizedBox(width: 8),
              Text('Ask Studio AI',
                  style: TextStyle(fontWeight: FontWeight.w900)),
            ],
          ),
          const SizedBox(height: 10),
          const Text(
              'Need a video idea or a catchy title? My free LLM model is ready to help!',
              style: TextStyle(fontSize: 13, height: 1.4)),
          const SizedBox(height: 15),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
                backgroundColor: Colors.white,
                foregroundColor: Colors.black,
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8))),
            onPressed: () {},
            child: const Text('START CHAT',
                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
          )
        ],
      ),
    );
  }
}

class CreateScreen extends StatelessWidget {
  const CreateScreen({super.key});
  @override
  Widget build(BuildContext context) {
    return Container();
  }
}
