-- Migration 002: Add photo_url to pets for photo uploads
-- Safe to run multiple times.
ALTER TABLE pets ADD COLUMN IF NOT EXISTS photo_url TEXT;
