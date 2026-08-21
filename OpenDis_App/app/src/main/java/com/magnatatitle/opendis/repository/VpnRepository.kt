package com.magnatatitle.opendis.repository

import android.content.Context
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey
import com.magnatatitle.opendis.local.CredentialDao
import com.magnatatitle.opendis.domain.ProfileAnalyzer
import com.magnatatitle.opendis.domain.VpnBookHelper
import com.magnatatitle.opendis.model.VpnCredentials
import com.magnatatitle.opendis.model.VpnProfile
import dagger.hilt.android.qualifiers.ApplicationContext
import java.io.File
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class VpnRepository @Inject constructor(
    @ApplicationContext private val context: Context,
    private val credentialDao: CredentialDao
) {
    private val vpnDir: File
        get() = File(context.filesDir, "VPN").also { it.mkdirs() }

    private val vpnBookDir: File
        get() = File(vpnDir, "VPNBook").also { it.mkdirs() }

    private val encryptedPrefs by lazy {
        val masterKey = MasterKey.Builder(context)
            .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
            .build()

        EncryptedSharedPreferences.create(
            context,
            "opendis_secure_prefs",
            masterKey,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
        )
    }

    // ─── Perfis ───

    fun listProfiles(): List<VpnProfile> {
        val allProfiles = mutableListOf<VpnProfile>()
        
        // Perfis manuais
        val manual = vpnDir.listFiles { f -> f.extension == "ovpn" }?.map { file ->
            mapToFileProfile(file, false)
        } ?: emptyList()
        
        // Perfis VPNBook
        val vpnBook = vpnBookDir.listFiles { f -> f.extension == "ovpn" }?.map { file ->
            mapToFileProfile(file, true)
        } ?: emptyList()

        allProfiles.addAll(manual)
        allProfiles.addAll(vpnBook)
        
        return allProfiles.sortedBy { it.name.lowercase() }
    }

    private fun mapToFileProfile(file: File, isVpnBook: Boolean): VpnProfile {
        val (server, protocol) = ProfileAnalyzer.extractServerInfo(file)
        return VpnProfile(
            name = file.name,
            filePath = file.absolutePath,
            requiresAuth = ProfileAnalyzer.requiresCredentials(file),
            serverName = server,
            protocol = protocol,
            isVpnBook = isVpnBook
        )
    }

    /**
     * Importa um arquivo para o diretório interno e retorna o objeto VpnProfile.
     */
    fun importProfile(sourceFile: File): VpnProfile? {
        try {
            val destFile = File(vpnDir, sourceFile.name)
            sourceFile.copyTo(destFile, overwrite = true)
            return mapToFileProfile(destFile, false)
        } catch (e: Exception) {
            return null
        }
    }

    // ─── VPNBook ───

    suspend fun getRandomVpnProfile(): Triple<File, VpnCredentials, VpnProfile> {
        val credentials = VpnBookHelper.fetchCredentials()
            ?: throw RuntimeException("Não foi possível obter credenciais do VPNBook")

        val savedProfile = vpnBookDir.listFiles { f ->
            f.extension == "ovpn" && f.nameWithoutExtension.contains("us16")
        }?.firstOrNull()

        val profileFile = savedProfile ?: VpnBookHelper.downloadProfile(vpnBookDir)
            ?: throw RuntimeException("Não foi possível baixar perfil VPNBook")

        val vpnProfile = mapToFileProfile(profileFile, true)

        return Triple(profileFile, credentials, vpnProfile)
    }

    // ─── Credenciais ───

    fun getSavedCredentials(profileHash: String): VpnCredentials? {
        val encryptedUser = encryptedPrefs.getString("user_$profileHash", null)
        val encryptedPass = encryptedPrefs.getString("pass_$profileHash", null)
        if (encryptedUser != null && encryptedPass != null) {
            return VpnCredentials(encryptedUser, encryptedPass)
        }
        return null
    }

    fun saveCredentials(profileHash: String, credentials: VpnCredentials) {
        encryptedPrefs.edit()
            .putString("user_$profileHash", credentials.username)
            .putString("pass_$profileHash", credentials.password)
            .apply()
    }
}
