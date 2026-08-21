// model/VpnProfile.kt
package com.magnatatitle.opendis.model

import android.os.Parcelable
import kotlinx.parcelize.Parcelize

@Parcelize
data class VpnProfile(
    val id: Long = 0,
    val name: String,
    val filePath: String,     // caminho interno do .ovpn
    val requiresAuth: Boolean = false,
    val serverName: String? = null,
    val protocol: String? = null,
    val isVpnBook: Boolean = false
) : Parcelable
