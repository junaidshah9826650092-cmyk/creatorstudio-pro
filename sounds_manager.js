/* 
   Vitox Premium Sound Manager
   High-end UI audio feedback for a premium feel.
*/

const VitoxSounds = {
    // CDN links to high-quality, short UI sounds
    links: {
        click: 'https://assets.mixkit.co/active_storage/sfx/2568/2568-preview.mp3', // Clean click
        hover: 'https://assets.mixkit.co/active_storage/sfx/2571/2571-preview.mp3', // Subtle hover
        success: 'https://assets.mixkit.co/active_storage/sfx/2000/2000-preview.mp3', // Achievement/Reward
        notify: 'https://assets.mixkit.co/active_storage/sfx/2358/2358-preview.mp3', // New message/alert
        slide: 'https://assets.mixkit.co/active_storage/sfx/2573/2573-preview.mp3'  // Sidebar/Menu slide
    },
    
    // Play sound by name
    play: function(name) {
        if (!this.links[name]) return;
        const audio = new Audio(this.links[name]);
        audio.volume = 0.5;
        audio.play().catch(e => console.log("Audio play blocked: Use interaction first."));
    },

    // Initialize Global Event Listeners for common interactions
    init: function() {
        document.addEventListener('click', (e) => {
            const el = e.target.closest('button, a, .clickable, .icon-btn');
            if (el) this.play('click');
        });
    }
};

// Auto-init on load
window.addEventListener('load', () => VitoxSounds.init());
