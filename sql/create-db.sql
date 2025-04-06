-- Drop existing tables if they exist
DROP TABLE IF EXISTS lottery_entries;
DROP TABLE IF EXISTS lottery;
DROP TABLE IF EXISTS competition;
DROP TABLE IF EXISTS member;

CREATE TABLE member
( _id SERIAL PRIMARY KEY,
  rsn varchar(12) NOT NULL,
  discord_id_num bigint UNIQUE,
  discord_id varchar(37),
  membership_level integer CHECK (membership_level >= 0 AND membership_level <= 8),
  join_date date,
  special_status varchar(50),
  previous_rsn TEXT [],
  alt_rsn TEXT [],
  on_leave boolean,
  active boolean,
  skill_comp_pts integer,
  skill_comp_pts_life integer,
  boss_comp_pts integer,
  boss_comp_pts_life integer,
  loc varchar(10),
  timezone varchar(10),
  notes varchar(512)
);

CREATE TABLE competition
( 
    comp_id SERIAL PRIMARY KEY,
    comp_name varchar(50),
    comp_type varchar(20),
    metric varchar(50),
    start_date timestamp,
    end_date timestamp,
    winner integer,
    second_place integer,
    third_place integer,
    CONSTRAINT fk_member_id
      FOREIGN KEY(winner) 
	  REFERENCES member(_id),
    CONSTRAINT fk_second_place
      FOREIGN KEY(second_place)
      REFERENCES member(_id),
    CONSTRAINT fk_third_place
      FOREIGN KEY(third_place)
      REFERENCES member(_id)
);

CREATE INDEX idx_competition_type ON competition(comp_type);
CREATE INDEX idx_competition_dates ON competition(start_date, end_date);

CREATE TABLE lottery
(
    lottery_id SERIAL PRIMARY KEY,
    start_date timestamp NOT NULL,
    end_date timestamp NOT NULL,
    entry_fee integer NOT NULL CHECK (entry_fee >= 0),
    max_entries integer NOT NULL CHECK (max_entries > 0),
    winner_id integer,
    CONSTRAINT fk_winner_id
        FOREIGN KEY(winner_id)
        REFERENCES member(_id)
);

CREATE TABLE lottery_entries
(
    lottery_id integer,
    member_id integer,
    entries_purchased integer NOT NULL CHECK (entries_purchased > 0),
    PRIMARY KEY (lottery_id, member_id),
    CONSTRAINT fk_lottery_id
        FOREIGN KEY(lottery_id)
        REFERENCES lottery(lottery_id),
    CONSTRAINT fk_member_id
        FOREIGN KEY(member_id)
        REFERENCES member(_id)
);