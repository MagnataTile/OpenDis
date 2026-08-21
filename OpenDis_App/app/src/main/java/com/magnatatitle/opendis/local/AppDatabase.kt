// data/local/AppDatabase.kt
package com.magnatatitle.opendis.local

import androidx.room.Database
import androidx.room.RoomDatabase

@Database(
    entities = [CredentialEntity::class],
    version = 1,
    exportSchema = false
)
abstract class AppDatabase : RoomDatabase() {
    abstract fun credentialDao(): CredentialDao
}
