package com.magnatatitle.opendis.di

import android.content.Context
import androidx.room.Room
import com.magnatatitle.opendis.local.AppDatabase
import com.magnatatitle.opendis.local.CredentialDao
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {

    @Provides
    @Singleton
    fun provideDatabase(@ApplicationContext context: Context): AppDatabase {
        return Room.databaseBuilder(
            context,
            AppDatabase::class.java,
            "opendis_db"
        ).build()
    }

    @Provides
    fun provideCredentialDao(database: AppDatabase): CredentialDao {
        return database.credentialDao()
    }
}
