drop table if exists entries;
create table entries (
  id serial primary key not null,
  date timestamp with time zone not null default now(),
  title varchar(80) not null,
  content text not null
);
