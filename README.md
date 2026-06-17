[install.sh.](https://github.com/user-attachments/files/29030483/install.sh.txt)
#!/bin/sh
cd /tmp
rm -rf plugin_build
mkdir -p plugin_build/usr/lib/enigma2/python/Plugins/Extensions/ChannelInfo
mkdir -p plugin_build/CONTROL

cat > plugin_build/usr/lib/enigma2/python/Plugins/Extensions/ChannelInfo/plugin.py << 'EOF'
from Plugins.Plugin import PluginDescriptor
from .info_screen import ChannelInfoScreen
from .graph_screen import BitrateGraphScreen

def main_info(session, **kwargs):
    session.open(ChannelInfoScreen)

def main_graph(session, **kwargs):
    session.open(BitrateGraphScreen)

def Plugins(**kwargs):
    return [
        PluginDescriptor(name="معلومات القناة المتقدمة", description="عرض معلومات كاملة مع رسم بياني", where=PluginDescriptor.WHERE_PLUGINMENU, fnc=main_info),
        PluginDescriptor(name="رسم بياني للبت ريت", description="عرض رسم بياني لمعدل البت المتغير", where=PluginDescriptor.WHERE_PLUGINMENU, fnc=main_graph)
    ]
EOF

cat > plugin_build/usr/lib/enigma2/python/Plugins/Extensions/ChannelInfo/info_screen.py << 'EOF'
from Screens.Screen import Screen
from Components.Label import Label
from enigma import iServiceInformation
from Screens.InfoBar import InfoBar

class ChannelInfoScreen(Screen):
    skin = """
        <screen position="center,center" size="760,520" title="معلومات القناة" backgroundColor="#0a0a0a" alpha="230">
            <widget name="channel_name" position="30,30" size="700,55" font="Regular;30" foregroundColor="#00ff88" halign="center"/>
            <widget name="video_info" position="30,120" size="700,45" font="Regular;22" foregroundColor="#ffffff"/>
            <widget name="resolution_fps" position="30,170" size="700,45" font="Regular;22" foregroundColor="#66ccff"/>
            <widget name="bitrate" position="30,220" size="700,45" font="Regular;22" foregroundColor="#ffdd00"/>
            <widget name="audio_info" position="30,300" size="700,45" font="Regular;20" foregroundColor="#ff9933"/>
            <widget name="extra_info" position="30,355" size="700,80" font="Regular;18" foregroundColor="#aaaaaa"/>
            <widget name="exit_hint" position="30,470" size="700,35" font="Regular;16" foregroundColor="#666666" halign="center"/>
        </screen>
    """
    def __init__(self, session):
        Screen.__init__(self, session)
        self["channel_name"] = Label("")
        self["video_info"] = Label("")
        self["resolution_fps"] = Label("")
        self["bitrate"] = Label("")
        self["audio_info"] = Label("")
        self["extra_info"] = Label("")
        self["exit_hint"] = Label("اضغط EXIT للخروج")
        self.get_channel_info()
    def get_channel_info(self):
        try:
            service = InfoBar.instance and InfoBar.instance.getCurrentService()
            if not service:
                self["channel_name"].setText("لا توجد قناة")
                return
            info = service.info()
            if not info:
                self["channel_name"].setText("لا يمكن جلب المعلومات")
                return
            service_ref = InfoBar.instance.getCurrentServiceRef()
            channel_name = service_ref.getServiceName() if service_ref else "غير معروف"
            if isinstance(channel_name, bytes):
                channel_name = channel_name.decode('utf-8', errors='ignore')
            self["channel_name"].setText(f"📺 {channel_name}")
            video_width = info.getInfo(iServiceInformation.sVideoWidth)
            video_height = info.getInfo(iServiceInformation.sVideoHeight)
            video_fps = info.getInfo(iServiceInformation.sFrameRate)
            video_codec = info.getInfoString(iServiceInformation.sVideoCodec)
            if isinstance(video_codec, bytes):
                video_codec = video_codec.decode('utf-8', errors='ignore')
            if video_width > 0 and video_height > 0:
                quality = "4K" if video_width >= 3840 else "FHD" if video_width >= 1920 else "HD" if video_width >= 1280 else "SD"
                self["video_info"].setText(f"🎬 {video_codec or 'غير معروف'} | {quality}")
                self["resolution_fps"].setText(f"📐 {video_width}×{video_height} | {video_fps} FPS")
            else:
                self["video_info"].setText("🎬 الفيديو: غير متاح")
                self["resolution_fps"].setText("📐 الدقة: غير متاحة")
            bitrate = info.getInfo(iServiceInformation.sBitrate) if hasattr(iServiceInformation, 'sBitrate') else 0
            if bitrate > 0:
                self["bitrate"].setText(f"⚡ معدل البت: {bitrate/1000:.2f} Mbps")
            else:
                self["bitrate"].setText("⚡ معدل البت: غير متاح")
            audio_codec = info.getInfoString(iServiceInformation.sAudioCodec)
            if isinstance(audio_codec, bytes):
                audio_codec = audio_codec.decode('utf-8', errors='ignore')
            self["audio_info"].setText(f"🔊 الصوت: {audio_codec or 'غير معروف'}")
            self["extra_info"].setText("📡 جاهز")
        except Exception as e:
            self["channel_name"].setText(f"❌ خطأ: {str(e)}")
    def exit(self):
        self.close()
EOF

cat > plugin_build/usr/lib/enigma2/python/Plugins/Extensions/ChannelInfo/graph_screen.py << 'EOF'
from Screens.Screen import Screen
from Components.Label import Label
from enigma import iServiceInformation
from Screens.InfoBar import InfoBar

class BitrateGraphScreen(Screen):
    skin = """
        <screen position="center,center" size="800,580" title="رسم بياني" backgroundColor="#0a0a0a" alpha="240">
            <widget name="current_bitrate" position="20,80" size="760,35" font="Regular;20" foregroundColor="#ffdd00" halign="center"/>
            <widget name="graph_lines" position="40,140" size="720,300" font="Regular;14" foregroundColor="#00ff88"/>
            <widget name="stats" position="20,460" size="760,60" font="Regular;16" foregroundColor="#aaaaaa"/>
        </screen>
    """
    def __init__(self, session):
        Screen.__init__(self, session)
        self["current_bitrate"] = Label("جاري جمع البيانات...")
        self["graph_lines"] = Label("")
        self["stats"] = Label("")
        self.bitrate_history = []
        self.update_timer = None
        self.start_updates()
    def start_updates(self):
        self.update_data()
        from twisted.internet import reactor
        self.update_timer = reactor.callLater(5, self.start_updates)
    def update_data(self):
        try:
            service = InfoBar.instance and InfoBar.instance.getCurrentService()
            if not service:
                return
            info = service.info()
            if not info:
                return
            bitrate = info.getInfo(iServiceInformation.sBitrate) if hasattr(iServiceInformation, 'sBitrate') else 0
            if bitrate > 0:
                bitrate_mb = bitrate / 1000.0
                self["current_bitrate"].setText(f"⚡ {bitrate_mb:.2f} Mbps")
                self.bitrate_history.append(bitrate_mb)
                if len(self.bitrate_history) > 60:
                    self.bitrate_history.pop(0)
                self.update_graph()
                if len(self.bitrate_history) > 1:
                    avg = sum(self.bitrate_history) / len(self.bitrate_history)
                    self["stats"].setText(f"📊 متوسط: {avg:.2f} Mbps")
        except:
            pass
    def update_graph(self):
        if not self.bitrate_history:
            return
        height = 20
        width = 60
        max_val = max(self.bitrate_history) or 1
        min_val = min(self.bitrate_history) or 0
        range_val = max_val - min_val or 1
        graph = []
        for i in range(height):
            line = ""
            for j in range(min(width, len(self.bitrate_history))):
                idx = len(self.bitrate_history) - width + j if len(self.bitrate_history) > width else j
                val = self.bitrate_history[idx]
                normalized = (val - min_val) / range_val
                line += "█" if normalized >= (1 - i/height) else "░"
            graph.append(line)
        self["graph_lines"].setText("\n".join(graph))
    def exit(self):
        if self.update_timer:
            self.update_timer.cancel()
        self.close()
EOF

cat > plugin_build/usr/lib/enigma2/python/Plugins/Extensions/ChannelInfo/__init__.py << 'EOF'
# -*- coding: utf-8 -*-
EOF

cat > plugin_build/CONTROL/control << 'EOF'
Package: enigma2-plugin-extensions-channelinfo
Version: 3.0
Description: معلومات متقدمة مع رسم بياني
Section: extras
Priority: optional
Maintainer: YourName
Architecture: all
OE: enigma2
Depends: enigma2 (>= 3.0), python3-core, python3-twisted
EOF

cd plugin_build
tar -czf control.tar.gz -C CONTROL control
tar -czf data.tar.gz -C usr .
echo "2.0" > debian-binary
ar -r /tmp/channelinfo.ipk debian-binary control.tar.gz data.tar.gz
cd /tmp
opkg install channelinfo.ipk
rm -rf /tmp/plugin_build
rm -f channelinfo.ipk
killall -9 enigma2
echo "✅ تم تثبيت البلاجن بنجاح!"
