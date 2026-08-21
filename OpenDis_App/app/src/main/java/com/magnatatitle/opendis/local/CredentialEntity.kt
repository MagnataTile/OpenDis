// data/local/CredentialEntity.kt
package com.magnatatitle.opendis.local

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "saved_credentials")
data class CredentialEntity(
    @PrimaryKey
    val profileHash: String,    // SHA-256 do conteúdo do .ovpn
    val username: String,
    val password: String,       // criptografado com EncryptedSharedPreferences
    val createdAt: Long = System.currentTimeMillis()
)
