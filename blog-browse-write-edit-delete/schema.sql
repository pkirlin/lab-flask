drop table if exists entries;
create table entries (
  id integer primary key not null,
  date datetime not null,
  title varchar(80) not null,
  content text not null
);
