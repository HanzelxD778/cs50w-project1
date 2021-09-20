CREATE TABLE books (
  id integer serial primary key,
  isbn varchar,
  title varchar,
  author varchar,
  year varchar
)

CREATE TABLE reviews (
  id serial primary key,
  user_id integer,
  book_id integer,
  review varchar,
  rating varchar,
  constraint fk_user_id foreign key (user_id) references users(id_user),
  constraint fk_book_id foreign key (book_id) references books(id)
)