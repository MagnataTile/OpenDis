// model/VpnConnectionState.kt
package com.magnatatitle.opendis.model

sealed class VpnConnectionState {
    object Disconnected : VpnConnectionState()
    object Connecting : VpnConnectionState()
    object Connected : VpnConnectionState()
    data class Error(val message: String) : VpnConnectionState()
    object Completed : VpnConnectionState()
}
