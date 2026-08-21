// data/local/CredentialDao.kt
package com.magnatatitle.opendis.local

import androidx.room.*

@Dao
interface CredentialDao {

    @Query("SELECT * FROM saved_credentials WHERE profileHash = :hash")
    suspend fun getByProfileHash(hash: String): CredentialEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(credential: CredentialEntity)

    @Query("DELETE FROM saved_credentials WHERE profileHash = :hash")
    suspend fun deleteByProfileHash(hash: String)
}
