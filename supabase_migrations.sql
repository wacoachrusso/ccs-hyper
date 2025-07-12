-- CCS Hyper Database Schema for Supabase
-- This file contains SQL migrations for setting up the Supabase database

-- Enable Row Level Security
-- ALTER DATABASE postgres SET "app.jwt_secret" TO 'your-jwt-secret'; -- This may require admin privileges not available in the SQL editor.

-- Create secure schema
CREATE SCHEMA IF NOT EXISTS private;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create profiles table for user information
CREATE TABLE IF NOT EXISTS public.profiles (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users NOT NULL,
  username TEXT UNIQUE,
  full_name TEXT,
  avatar_url TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Create pairings table
CREATE TABLE IF NOT EXISTS public.pairings (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users NOT NULL,
  pairing_code TEXT NOT NULL,
  start_date TIMESTAMPTZ NOT NULL,
  end_date TIMESTAMPTZ NOT NULL,
  block_time INTEGER,
  credit_time INTEGER,
  trip_value TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Create flights table
CREATE TABLE IF NOT EXISTS public.flights (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  pairing_id UUID REFERENCES public.pairings NOT NULL,
  flight_number TEXT NOT NULL,
  departure_airport TEXT NOT NULL,
  arrival_airport TEXT NOT NULL,
  scheduled_departure TIMESTAMPTZ NOT NULL,
  scheduled_arrival TIMESTAMPTZ NOT NULL,
  aircraft_type TEXT,
  actual_departure TIMESTAMPTZ,
  actual_arrival TIMESTAMPTZ,
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Create crew members table
CREATE TABLE IF NOT EXISTS public.crew_members (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  employee_id TEXT UNIQUE,
  base TEXT,
  seniority TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Create flight crew association table
CREATE TABLE IF NOT EXISTS public.flight_crew (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  flight_id UUID REFERENCES public.flights NOT NULL,
  crew_member_id UUID REFERENCES public.crew_members NOT NULL,
  position TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(flight_id, crew_member_id)
);

-- Create user crew lists table (for Do Not Fly and Friends lists)
CREATE TABLE IF NOT EXISTS public.user_crew_lists (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users NOT NULL,
  crew_member_id UUID REFERENCES public.crew_members NOT NULL,
  list_type TEXT NOT NULL CHECK (list_type IN ('do_not_fly', 'friends')),
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(user_id, crew_member_id, list_type)
);

-- Create statistics table
CREATE TABLE IF NOT EXISTS public.statistics (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users NOT NULL,
  month INTEGER NOT NULL,
  year INTEGER NOT NULL,
  total_block INTEGER,
  total_credit INTEGER,
  flights_count INTEGER,
  miles_flown INTEGER,
  aircraft_types JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(user_id, month, year)
);

-- Create settings table for user preferences
CREATE TABLE IF NOT EXISTS public.settings (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users NOT NULL,
  notification_email BOOLEAN DEFAULT true,
  notification_push BOOLEAN DEFAULT true,
  theme TEXT DEFAULT 'dark',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Set up Row Level Security (RLS) policies

-- Profiles: Users can only read/update their own profiles
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own profile" 
  ON public.profiles FOR SELECT 
  USING (auth.uid() = user_id);

CREATE POLICY "Users can update their own profile" 
  ON public.profiles FOR UPDATE 
  USING (auth.uid() = user_id);

-- Pairings: Users can only CRUD their own pairings
ALTER TABLE public.pairings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own pairings" 
  ON public.pairings FOR SELECT 
  USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own pairings" 
  ON public.pairings FOR INSERT 
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own pairings" 
  ON public.pairings FOR UPDATE 
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own pairings" 
  ON public.pairings FOR DELETE 
  USING (auth.uid() = user_id);

-- Flights: Access through pairings ownership
ALTER TABLE public.flights ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view flights in their pairings" 
  ON public.flights FOR SELECT 
  USING (EXISTS (
    SELECT 1 FROM public.pairings 
    WHERE public.pairings.id = public.flights.pairing_id 
    AND public.pairings.user_id = auth.uid()
  ));

CREATE POLICY "Users can create flights in their pairings" 
  ON public.flights FOR INSERT 
  WITH CHECK (EXISTS (
    SELECT 1 FROM public.pairings 
    WHERE public.pairings.id = public.flights.pairing_id 
    AND public.pairings.user_id = auth.uid()
  ));

CREATE POLICY "Users can update flights in their pairings" 
  ON public.flights FOR UPDATE 
  USING (EXISTS (
    SELECT 1 FROM public.pairings 
    WHERE public.pairings.id = public.flights.pairing_id 
    AND public.pairings.user_id = auth.uid()
  ));

CREATE POLICY "Users can delete flights in their pairings" 
  ON public.flights FOR DELETE 
  USING (EXISTS (
    SELECT 1 FROM public.pairings 
    WHERE public.pairings.id = public.flights.pairing_id 
    AND public.pairings.user_id = auth.uid()
  ));

-- Crew Members: Read-only for all authenticated users, admin for CREATE/UPDATE/DELETE
ALTER TABLE public.crew_members ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view all crew members" 
  ON public.crew_members FOR SELECT 
  TO authenticated 
  USING (true);

-- User Crew Lists: Users can only CRUD their own lists
ALTER TABLE public.user_crew_lists ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own crew lists" 
  ON public.user_crew_lists FOR SELECT 
  USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own crew lists" 
  ON public.user_crew_lists FOR INSERT 
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own crew lists" 
  ON public.user_crew_lists FOR UPDATE 
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete from their own crew lists" 
  ON public.user_crew_lists FOR DELETE 
  USING (auth.uid() = user_id);

-- Statistics: Users can only CRUD their own statistics
ALTER TABLE public.statistics ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own statistics" 
  ON public.statistics FOR SELECT 
  USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own statistics" 
  ON public.statistics FOR INSERT 
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own statistics" 
  ON public.statistics FOR UPDATE 
  USING (auth.uid() = user_id);

-- Settings: Users can only CRUD their own settings
ALTER TABLE public.settings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own settings" 
  ON public.settings FOR SELECT 
  USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own settings" 
  ON public.settings FOR INSERT 
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own settings" 
  ON public.settings FOR UPDATE 
  USING (auth.uid() = user_id);

-- Create function for handling user registration
CREATE OR REPLACE FUNCTION public.handle_new_user() 
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (user_id, username, full_name)
  VALUES (
    NEW.id, 
    NEW.raw_user_meta_data->>'username',
    NEW.raw_user_meta_data->>'full_name'
  );
  
  INSERT INTO public.settings (user_id)
  VALUES (NEW.id);
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create trigger for new user registration
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();

-- Function to update modified timestamp
CREATE OR REPLACE FUNCTION update_modified_column() 
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW; 
END;
$$ LANGUAGE plpgsql;

-- Add triggers to update timestamps
CREATE TRIGGER set_timestamp_profiles
BEFORE UPDATE ON public.profiles
FOR EACH ROW EXECUTE PROCEDURE update_modified_column();

CREATE TRIGGER set_timestamp_pairings
BEFORE UPDATE ON public.pairings
FOR EACH ROW EXECUTE PROCEDURE update_modified_column();

CREATE TRIGGER set_timestamp_user_crew_lists
BEFORE UPDATE ON public.user_crew_lists
FOR EACH ROW EXECUTE PROCEDURE update_modified_column();

CREATE TRIGGER set_timestamp_settings
BEFORE UPDATE ON public.settings
FOR EACH ROW EXECUTE PROCEDURE update_modified_column();

CREATE TRIGGER set_timestamp_statistics
BEFORE UPDATE ON public.statistics
FOR EACH ROW EXECUTE PROCEDURE update_modified_column();
