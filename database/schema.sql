create extension if not exists "pgcrypto";

create table if not exists users (
    id uuid primary key default gen_random_uuid(),
    email text unique not null,
    full_name text,
    phone text,
    avatar_url text,
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);

create table if not exists staff_roles (
    id serial primary key,
    role_key text unique not null,
    label text not null
);

create table if not exists admins (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references users(id) on delete cascade,
    email text unique not null,
    role_id int references staff_roles(id),
    is_approved boolean default false,
    created_at timestamptz default now()
);

create table if not exists catalogues (
    id uuid primary key default gen_random_uuid(),
    name text not null,
    slug text unique not null,
    description text,
    cover_image_url text,
    is_featured boolean default false
);
create table if not exists products (
    id uuid primary key default gen_random_uuid(),
    catalogue_id uuid references catalogues(id) on delete set null,
    name text not null,
    slug text unique not null,
    description text,
    price_inr numeric(12,2),
    hero_image_url text,
    is_featured boolean default false,
    created_at timestamptz default now()
);
create table if not exists product_media (
    id uuid primary key default gen_random_uuid(),
    product_id uuid references products(id) on delete cascade,
    media_url text not null,
    media_type text not null,
    sort_order int default 0
);
create table if not exists catalogue_products (
    catalogue_id uuid references catalogues(id) on delete cascade,
    product_id uuid references products(id) on delete cascade,
    primary key(catalogue_id, product_id)
);
create table if not exists banners (
    id uuid primary key default gen_random_uuid(),
    title text,
    subtitle text,
    image_url text,
    video_url text,
    cta_label text,
    cta_url text,
    is_active boolean default true
);
create table if not exists homepage_sections (
    id uuid primary key default gen_random_uuid(),
    title text,
    subtitle text,
    body text,
    order_index int default 0,
    is_active boolean default true
);
create table if not exists wishlist (
    user_id uuid references users(id) on delete cascade,
    product_id uuid references products(id) on delete cascade,
    created_at timestamptz default now(),
    primary key(user_id, product_id)
);
create table if not exists recently_viewed (
    user_id uuid references users(id) on delete cascade,
    product_id uuid references products(id) on delete cascade,
    viewed_at timestamptz default now(),
    primary key(user_id, product_id)
);
create table if not exists inquiries (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references users(id) on delete set null,
    product_id uuid references products(id) on delete set null,
    message text not null,
    source text default 'web',
    created_at timestamptz default now()
);
create table if not exists social_links (
    id serial primary key,
    platform text unique not null,
    url text not null,
    is_active boolean default true
);
create table if not exists settings (
    key text primary key,
    value jsonb not null
);

create index if not exists idx_products_catalogue_id on products(catalogue_id);
create index if not exists idx_products_featured on products(is_featured);
create index if not exists idx_catalogues_featured on catalogues(is_featured);
create index if not exists idx_banners_active on banners(is_active);
create index if not exists idx_homepage_sections_order on homepage_sections(order_index);
create index if not exists idx_inquiries_created_at on inquiries(created_at desc);
