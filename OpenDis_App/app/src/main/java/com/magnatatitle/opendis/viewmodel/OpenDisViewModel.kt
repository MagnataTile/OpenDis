package com.magnatatitle.opendis.viewmodel

import android.app.ActivityManager
import android.app.Application
import android.content.Context
import android.content.Intent
import android.net.VpnService
import android.os.Build
import android.util.Log
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.magnatatitle.opendis.domain.ProfileAnalyzer
import com.magnatatitle.opendis.domain.PublicIpChecker
import com.magnatatitle.opendis.model.VpnConnectionState
import com.magnatatitle.opendis.model.VpnCredentials
import com.magnatatitle.opendis.model.VpnProfile
import com.magnatatitle.opendis.repository.VpnRepository
import com.magnatatitle.opendis.vpn.OpenDisNotification
import com.magnatatitle.opendis.vpn.OpenDisVpnService
import com.magnatatitle.opendis.vpn.VpnEventBus
import com.tim.openvpn.configuration.OpenVPNConfig
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import javax.inject.Inject

@HiltViewModel
class OpenDisViewModel @Inject constructor(
    application: Application,
    private val repository: VpnRepository
) : AndroidViewModel(application) {

    companion object {
        private const val TAG = "OpenDis/ViewModel"
        private const val CONNECTION_TIMEOUT_MS = 60000L
        private const val IP_CHECK_INTERVAL_MS = 2500L
        private const val DISCORD_STABILIZATION_MS = 15000L 
    }

    // ─── Estados da UI ───

    private val _profiles = MutableStateFlow<List<VpnProfile>>(emptyList())
    val profiles: StateFlow<List<VpnProfile>> = _profiles.asStateFlow()

    private val _connectionState = MutableStateFlow<VpnConnectionState>(VpnConnectionState.Disconnected)
    val connectionState: StateFlow<VpnConnectionState> = _connectionState.asStateFlow()

    private val _logs = MutableStateFlow<List<String>>(listOf("[OpenDis] Inicializando Sistema..."))
    val logs: StateFlow<List<String>> = _logs.asStateFlow()

    private val _currentIp = MutableStateFlow<String?>(null)
    val currentIp: StateFlow<String?> = _currentIp.asStateFlow()

    private val _selectedProfile = MutableStateFlow<VpnProfile?>(null)
    val selectedProfile: StateFlow<VpnProfile?> = _selectedProfile.asStateFlow()

    private val _isVpnAuthorized = MutableStateFlow(false)
    val isVpnAuthorized: StateFlow<Boolean> = _isVpnAuthorized.asStateFlow()

    // Estado para preenchimento automático de credenciais
    private val _savedCredentials = MutableStateFlow<VpnCredentials?>(null)
    val savedCredentials: StateFlow<VpnCredentials?> = _savedCredentials.asStateFlow()

    // Estados internos
    private var currentCredentials: VpnCredentials? = null
    private var flowJob: Job? = null

    init {
        detectEnvironment()
        loadProfiles()
        checkInitialIp()
        checkVpnPermission()
        observeVpnEvents()
    }

    private fun addLog(message: String) {
        val timestamp = SimpleDateFormat("HH:mm:ss", Locale.getDefault()).format(Date())
        _logs.value = _logs.value + "[$timestamp] $message"
        Log.i(TAG, message)
    }

    private fun observeVpnEvents() {
        viewModelScope.launch {
            VpnEventBus.events.collect { message ->
                addLog(message)
            }
        }
    }

    private fun detectEnvironment() {
        val pm = getApplication<Application>().packageManager
        // Verificamos apenas o Discord, a VPN agora é interna/segura
        val apps = mapOf("com.discord" to "Discord")
        apps.forEach { (pkg, name) ->
            val installed = try { pm.getPackageInfo(pkg, 0); true } catch (e: Exception) { false }
            if (installed) {
                addLog("✅ $name detectado")
            } else {
                addLog("❌ $name não encontrado")
            }
        }
        addLog("🛡️ Sistema de Túnel Interno: Ativo")
    }

    fun isOpenVpnInstalled(): Boolean = true // Agora é interno

    fun loadProfiles() {
        _profiles.value = repository.listProfiles()
        addLog("📂 Perfil(is) .ovpn encontrados: ${_profiles.value.size}")
    }

    fun importAndSelectProfile(tempFile: File) {
        viewModelScope.launch {
            val imported = repository.importProfile(tempFile)
            if (imported != null) {
                loadProfiles()
                selectProfile(imported)
                addLog("✅ Perfil importado e selecionado: ${imported.name}")
            } else {
                addLog("❌ Falha ao importar perfil")
            }
        }
    }

    private fun checkInitialIp() {
        viewModelScope.launch {
            val ip = PublicIpChecker.getCurrentIp()
            _currentIp.value = ip
            if (ip != null) addLog("🌐 IP Original: $ip")
        }
    }

    fun selectProfile(profile: VpnProfile) {
        _selectedProfile.value = profile
        _savedCredentials.value = null
        currentCredentials = null
        addLog("📄 Perfil: ${profile.name}")
        
        if (profile.requiresAuth) {
            val hash = ProfileAnalyzer.computeHash(File(profile.filePath))
            val saved = repository.getSavedCredentials(hash)
            if (saved != null) {
                _savedCredentials.value = saved
                currentCredentials = saved
                addLog("🔑 Credenciais carregadas do armazenamento seguro")
            }
        }
        checkVpnPermission()
    }

    fun startVpnBookRandom() {
        viewModelScope.launch {
            try {
                addLog("🎲 VPN ALEATÓRIA: Obtendo dados do VPNBook...")
                val (profileFile, credentials, vpnProfile) = repository.getRandomVpnProfile()
                currentCredentials = credentials
                _savedCredentials.value = credentials
                _selectedProfile.value = vpnProfile

                // Sincroniza e salva as credenciais para que o fluxo manual também funcione
                val hash = ProfileAnalyzer.computeHash(profileFile)
                repository.saveCredentials(hash, credentials)
                addLog("💾 Credenciais VPNBook persistidas")

                addLog("✅ VPNBook: Perfil ${profileFile.name} pronto")
                checkVpnPermission()
            } catch (e: Exception) {
                addLog("❌ Erro VPNBook: ${e.message}")
            }
        }
    }

    fun submitCredentials(username: String, password: String, remember: Boolean) {
        val credentials = VpnCredentials(username, password)
        currentCredentials = credentials
        
        if (remember) {
            _selectedProfile.value?.let {
                val hash = ProfileAnalyzer.computeHash(File(it.filePath))
                repository.saveCredentials(hash, credentials)
                addLog("💾 Credenciais salvas com sucesso")
            }
        }
        checkVpnPermission()
    }

    fun setVpnAuthorized() {
        _isVpnAuthorized.value = true
        addLog("🔐 Autorização de Rede Concedida")
    }

    fun checkVpnPermission() {
        val intent = VpnService.prepare(getApplication())
        _isVpnAuthorized.value = (intent == null)
    }

    fun onVpnPermissionResult(granted: Boolean) {
        _isVpnAuthorized.value = granted
        addLog(if (granted) "🔐 Autorização de Rede Concedida" else "⚠️ Autorização Negada")
    }

    fun startFullFlow() {
        if (!_isVpnAuthorized.value) {
            addLog("⚠️ Rede não autorizada!")
            return
        }
        val profile = _selectedProfile.value ?: return

        flowJob?.cancel()
        flowJob = viewModelScope.launch {
            try {
                _connectionState.value = VpnConnectionState.Connecting
                addLog("🚀 Iniciando Fluxo Crítico...")

                // 1. OBRIGA O ENCERRAMENTO DO DISCORD
                addLog("🛑 Encerrando Discord (Obrigatório)...")
                killDiscord()
                delay(1000)

                // 2. SALVA O IP ORIGINAL PARA COMPARAÇÃO
                addLog("🔍 Capturando IP original para validação...")
                val originalIp = PublicIpChecker.getCurrentIp()
                _currentIp.value = originalIp
                if (originalIp == null) {
                    addLog("⚠️ Não foi possível obter o IP original, prosseguindo com cautela...")
                } else {
                    addLog("🌐 IP Original: $originalIp")
                }

                // 3. ESTABELECE A VPN
                addLog("📡 Estabelecendo túnel de rede...")
                startVpnService(profile)

                // 4. VERIFICA O TÚNEL (Compara Novo IP vs Original)
                val connected = waitForIpChange(originalIp)

                if (connected) {
                    // 5. ABRE O DISCORD
                    delay(1500)
                    openDiscord()
                    addLog("⏳ Estabilizando Discord (15s)...")
                    delay(DISCORD_STABILIZATION_MS)
                    
                    // 6. FINALIZAÇÃO
                    addLog("🔌 Encerrando conexão...")
                    disconnectVpn()
                    delay(3000)

                    _connectionState.value = VpnConnectionState.Completed
                    addLog("🎉 PROCESSO 100% CONCLUÍDO!")
                } else {
                    addLog("❌ FALHA: O IP não mudou após 25s (Túnel Falhou)")
                    _connectionState.value = VpnConnectionState.Error("Falha no Túnel")
                    disconnectVpn()
                }
            } catch (e: Exception) {
                addLog("❌ Erro: ${e.message}")
                _connectionState.value = VpnConnectionState.Error(e.message ?: "Erro")
                disconnectVpn()
            }
        }
    }

    private fun killDiscord() {
        try {
            val am = getApplication<Application>().getSystemService(Context.ACTIVITY_SERVICE) as ActivityManager
            am.killBackgroundProcesses("com.discord")
            Log.d(TAG, "Kill Discord signal sent")
        } catch (e: Exception) { }
    }

    private suspend fun waitForIpChange(originalIp: String?): Boolean {
        addLog("⏳ Validando mudança de IP público...")
        val startTime = System.currentTimeMillis()
        
        // Delay inicial para o sistema rotear os pacotes
        delay(4000)

        while (System.currentTimeMillis() - startTime < CONNECTION_TIMEOUT_MS) {
            val newIp = PublicIpChecker.getCurrentIp()
            Log.d(TAG, "Check IP: $newIp (Original: $originalIp)")
            
            if (newIp != null && newIp != originalIp) {
                _currentIp.value = newIp
                addLog("✅ IP ALTERADO! Novo IP: $newIp")
                _connectionState.value = VpnConnectionState.Connected
                return true
            }
            delay(IP_CHECK_INTERVAL_MS)
        }
        return false
    }

    private fun startVpnService(profile: VpnProfile) {
        val creds = currentCredentials ?: VpnCredentials("", "")
        val context = getApplication<Application>()
        
        addLog("⚡ Iniciando túnel seguro...")

        val profileFile = File(profile.filePath)
        var ovpnContent = if (profileFile.exists()) profileFile.readText() else ""

        // 1. Remover blocos <auth-user-pass>...</auth-user-pass> existentes para evitar duplicidade
        ovpnContent = ovpnContent.replace(Regex("<auth-user-pass>.*?</auth-user-pass>", 
            setOf(RegexOption.DOT_MATCHES_ALL, RegexOption.IGNORE_CASE)), "")

        // 2. Limpar diretivas auth-user-pass de linha única
        ovpnContent = ovpnContent.lines().filterNot { 
            it.trim().lowercase().startsWith("auth-user-pass") 
        }.joinToString("\n")

        // 3. Injetar credenciais no formato OpenVPN 3 para o motor C++
        // Fazemos isso sempre que houver usuário, garantindo que o fluxo manual seja idêntico ao automático
        if (creds.username.isNotBlank()) {
            ovpnContent += "\n<auth-user-pass>\n${creds.username}\n${creds.password}\n</auth-user-pass>\n"
        }

        val openVpnConfig = OpenVPNConfig(
            name = profile.name,
            configuration = ovpnContent
        )

        val intent = Intent(context, OpenDisVpnService::class.java).apply {
            putExtra(OpenDisVpnService.ACTION_KEY, OpenDisVpnService.ACTION_START_KEY)
            putExtra(OpenDisVpnService.CONFIGURATION_KEY, openVpnConfig)
            putExtra(OpenDisVpnService.NOTIFICATION_CLASS_KEY, OpenDisNotification::class.java.name)
            putExtra(OpenDisVpnService.EXTRA_PROFILE_NAME, profile.name)
        }

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) context.startForegroundService(intent)
        else context.startService(intent)
    }

    fun disconnectVpn() {
        val context = getApplication<Application>()
        val intent = Intent(context, OpenDisVpnService::class.java).apply {
            putExtra(OpenDisVpnService.ACTION_KEY, OpenDisVpnService.ACTION_STOP_KEY)
        }
        context.startService(intent)
        if (_connectionState.value !is VpnConnectionState.Error) {
            _connectionState.value = VpnConnectionState.Disconnected
        }
        addLog("🔌 VPN Desconectada")
    }

    fun openDiscord() {
        addLog("💬 Abrindo Discord...")
        val context = getApplication<Application>()
        val intent = context.packageManager.getLaunchIntentForPackage("com.discord")
            ?: Intent(Intent.ACTION_VIEW).apply { data = android.net.Uri.parse("market://details?id=com.discord") }
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        try { context.startActivity(intent); addLog("✅ Discord lançado") } catch (e: Exception) { }
    }

    fun reset() {
        flowJob?.cancel()
        _connectionState.value = VpnConnectionState.Disconnected
        _logs.value = listOf("[OpenDis] Estado Resetado")
        checkVpnPermission()
        checkInitialIp()
    }
}
