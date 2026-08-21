package com.magnatatitle.opendis.vpn

import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.asSharedFlow

/**
 * Barramento de eventos para logs do serviço VPN.
 */
object VpnEventBus {
    private val _events = MutableSharedFlow<String>(extraBufferCapacity = 64)
    val events = _events.asSharedFlow()

    fun log(message: String) {
        _events.tryEmit(message)
    }
}
