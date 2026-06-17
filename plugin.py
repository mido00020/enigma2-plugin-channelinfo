from Plugins.Plugin import PluginDescriptor
from .info_screen import ChannelInfoScreen
from .graph_screen import BitrateGraphScreen

def main_info(session, **kwargs):
    session.open(ChannelInfoScreen)

def main_graph(session, **kwargs):
    session.open(BitrateGraphScreen)

def Plugins(**kwargs):
    return [
        PluginDescriptor(
            name="معلومات القناة المتقدمة",
            description="عرض معلومات كاملة مع رسم بياني",
            where=PluginDescriptor.WHERE_PLUGINMENU,
            fnc=main_info
        ),
        PluginDescriptor(
            name="رسم بياني للبت ريت",
            description="عرض رسم بياني لمعدل البت المتغير",
            where=PluginDescriptor.WHERE_PLUGINMENU,
            fnc=main_graph
        )
    ]
