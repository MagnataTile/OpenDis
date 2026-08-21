package com.magnatatitle.opendis.vpn

import android.content.ContentResolver
import android.content.Context
import android.content.Intent
import android.net.ConnectivityManager
import android.net.VpnService
import android.os.Build
import android.os.Handler
import android.os.Message
import android.os.ParcelFileDescriptor
import com.magnatatitle.opendis.ui.MainActivity
import com.tim.basevpn.vpn.platform.logging.DefaultLogger
import com.tim.basevpn.vpn.platform.state.ConnectionState
import com.tim.openvpn.OpenVPNThreadv3
import com.tim.openvpn.configuration.OpenVPNConfig
import com.tim.openvpn.model.CIDRIP
import com.tim.openvpn.service.IOpenVPNService
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch

@AndroidEntryPoint
class OpenDisVpnService : VpnService(), Handler.Callback, IOpenVPNService {

    companion object {
        const val ACTION_CONNECT = "com.magnatatitle.opendis.CONNECT"
        const val ACTION_DISCONNECT = "com.magnatatitle.opendis.DISCONNECT"
        
        const val EXTRA_PROFILE_PATH = "profile_path"
        const val EXTRA_PROFILE_NAME = "profile_name"
        const val EXTRA_USERNAME = "username"
        const val EXTRA_PASSWORD = "password"

        const val CONFIGURATION_KEY = "CONFIGURATION_KEY"

        const val ACTION_KEY = "ACTION_KEY"
        const val ACTION_START_KEY = "ACTION_START_KEY"
        const val ACTION_STOP_KEY = "ACTION_STOP_KEY"
        const val NOTIFICATION_CLASS_KEY = "NOTIFICATION_CLASS_KEY"
    }

    private var management: OpenVPNThreadv3? = null
    private var config: OpenVPNConfig? = null
    private var job: Job? = null

    private var connectedNetworkName = "OpenDis"
    private val logger = DefaultLogger("OpenDisVpn")

    // ─── Estado da Configuração Dinâmica ───
    private var vpnMtu = 1500
    private var vpnLocalIp: CIDRIP? = null
    private var vpnLocalIPv6: String? = null
    private val vpnDnsServers = mutableListOf<String>()
    private val vpnRoutes = mutableListOf<CIDRIP>()

    private var notificationHelper: OpenDisNotification? = null

    private val serviceScope = kotlinx.coroutines.CoroutineScope(Dispatchers.Main + Job())


    // ─── Helper para Parse da Configuração ───

    private fun Intent.parseConfig(): OpenVPNConfig? {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            getParcelableExtra(CONFIGURATION_KEY, OpenVPNConfig::class.java)
        } else {
            @Suppress("DEPRECATION")
            getParcelableExtra(CONFIGURATION_KEY)
        }
    }

    // ─── Lifecycle ───

    override fun onCreate() {
        super.onCreate()
        VpnEventBus.log("⚙️ [VPN] Serviço nativo inicializado")
        notificationHelper = OpenDisNotification(this, getSystemService(Context.NOTIFICATION_SERVICE) as android.app.NotificationManager)
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val action = intent?.getStringExtra(ACTION_KEY)
        VpnEventBus.log("📥 [VPN] Action: $action")
        when (action) {
            ACTION_START_KEY -> {
                intent?.let { prepare(it) }
                start()
            }
            ACTION_STOP_KEY -> {
                stop()
            }
        }
        return START_STICKY
    }

    override fun handleMessage(msg: Message): Boolean {
        msg.callback?.run()
        return true
    }

    override fun onBind(intent: Intent?): android.os.IBinder? {
        return null
    }

    override fun onRevoke() {
        VpnEventBus.log("🔌 [VPN] Permissão revogada pelo sistema")
        stop()
        super.onRevoke()
    }

    fun prepare(intent: Intent) {
        config = intent.parseConfig()
        connectedNetworkName = intent.getStringExtra(EXTRA_PROFILE_NAME) ?: "OpenDis"
    }

    fun start() {
        VpnEventBus.log("🚀 [VPN] Iniciando motor OpenVPN...")
        startOpenVPN()
    }

    fun stop() {
        VpnEventBus.log("🛑 [VPN] Parando motor...")
        stopOpenVPN()
        stopSelf()
    }

    override fun onDestroy() {
        stopOpenVPN()
        serviceScope.cancel()
        super.onDestroy()
    }

    // ─── Motor OpenVPN ───

    private fun startOpenVPN() {
        showNotification()
        val conf = config ?: return

        // Limpar configuração anterior
        vpnMtu = 1500
        vpnLocalIp = null
        vpnLocalIPv6 = null
        vpnDnsServers.clear()
        vpnRoutes.clear()
        
        val configurationString = conf.configuration ?: ""
        
        management = OpenVPNThreadv3(this, configurationString, logger)
        
        job = serviceScope.launch(Dispatchers.IO) {
            try {
                VpnEventBus.log("⚙️ [VPN] Motor em execução")
                management?.run()
            } catch (e: Exception) {
                VpnEventBus.log("❌ [VPN] Erro no motor: ${e.message}")
            }
        }
    }

    private fun showNotification() {
        notificationHelper?.start()
    }

    private fun stopOpenVPN() {
        management?.stopVPN()
        management = null
        job?.cancel()
        job = null
        notificationHelper?.stop()
        VpnEventBus.log("🔌 [VPN] Motor desligado")
    }

    // ─── Interface IOpenVPNService (Chamado pelo Motor C++) ───

    override fun setMtu(mtu: Int) {
        VpnEventBus.log("📏 [VPN] MTU: $mtu")
        this.vpnMtu = mtu
    }

    override fun addDNS(dns: String?) {
        dns?.let { 
            VpnEventBus.log("🔍 [VPN] DNS: $it")
            if (!vpnDnsServers.contains(it)) vpnDnsServers.add(it)
        }
    }

    override fun addRoute(route: CIDRIP?, include: Boolean) {
        route?.let { 
            VpnEventBus.log("🛤️ [VPN] Rota: ${it.ip}/${it.len} (incluir: $include)")
            if (include && !vpnRoutes.contains(it)) vpnRoutes.add(it)
        }
    }

    override fun addRoute(dest: String?, mask: String?, gateway: String?, device: String?) {
        VpnEventBus.log("🛤️ [VPN] Rota: $dest $mask via $gateway")
        dest?.let { ip ->
            mask?.let { msk ->
                val len = calculatePrefixLength(msk)
                val route = CIDRIP(ip, len)
                if (!vpnRoutes.contains(route)) vpnRoutes.add(route)
            }
        }
    }

    private fun calculatePrefixLength(mask: String): Int {
        return try {
            val parts = mask.split(".")
            var length = 0
            for (part in parts) {
                var octet = part.toInt()
                while (octet > 0) {
                    if (octet and 0x80 != 0) length++
                    else break
                    octet = (octet shl 1) and 0xFF
                }
            }
            length
        } catch (e: Exception) {
            32
        }
    }

    override fun addRoutev6(network: String?, device: String?) {
        VpnEventBus.log("🛤️ [VPN] Rota IPv6: $network")
    }

    override fun setDomain(domain: String?) {
        VpnEventBus.log("🌐 [VPN] Domínio: $domain")
    }

    override fun addHttpProxy(proxy: String?, port: Int): Boolean = false

    override fun openTun(): ParcelFileDescriptor? {
        VpnEventBus.log("🔓 [VPN] Abrindo interface TUN dinamicamente...")
        val builder = Builder()
            .setSession(connectedNetworkName)
            .setMtu(vpnMtu)

        vpnLocalIp?.let { 
            builder.addAddress(it.ip, it.len)
        } ?: builder.addAddress("10.8.0.2", 24)

        if (vpnRoutes.isEmpty()) {
            builder.addRoute("0.0.0.0", 0)
        } else {
            vpnRoutes.forEach { route ->
                try {
                    builder.addRoute(route.ip, route.len)
                } catch (e: Exception) {
                    VpnEventBus.log("⚠️ [VPN] Erro ao adicionar rota: ${route.ip}/${route.len}")
                }
            }
        }

        if (vpnDnsServers.isEmpty()) {
            builder.addDnsServer("8.8.8.8")
        } else {
            vpnDnsServers.forEach { dns ->
                try {
                    builder.addDnsServer(dns)
                } catch (e: Exception) {
                    VpnEventBus.log("⚠️ [VPN] Erro ao adicionar DNS: $dns")
                }
            }
        }
            
        val pfd = builder.establish()
        if (pfd != null) VpnEventBus.log("✅ [VPN] tun0 estabelecida dinamicamente")
        return pfd
    }

    override fun setLocalIP(cidrip: CIDRIP?) {
        cidrip?.let { 
            VpnEventBus.log("🏠 [VPN] IP Local: ${it.ip}/${it.len}")
            this.vpnLocalIp = it
        }
    }

    override fun setLocalIPv6(ipv6addr: String?) {
        VpnEventBus.log("🏠 [VPN] IPv6 Local: $ipv6addr")
        this.vpnLocalIPv6 = ipv6addr
    }

    override fun protectFd(fd: Int): Boolean {
        return protect(fd)
    }

    override fun triggerSso(info: String?) {
    }

    override val ctResolver: ContentResolver
        get() = contentResolver

    override val connectivityManager: ConnectivityManager
        get() = getSystemService(CONNECTIVITY_SERVICE) as ConnectivityManager

    override fun openvpnStopped() {
        VpnEventBus.log("ℹ️ [VPN] OpenVPN parou")
        updateState(ConnectionState.DISCONNECTED)
    }

    override fun updateStateThread(state: ConnectionState) {
        VpnEventBus.log("📊 [VPN] Estado: $state")
        updateState(state)
    }

    private fun updateState(state: ConnectionState) {
        // Implementar se necessário notificar a UI de outra forma
    }
}

