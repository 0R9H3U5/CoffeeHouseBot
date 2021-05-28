CREATE TABLE member
( _id integer PRIMARY KEY,
  rsn varchar(12) NOT NULL,
  discord_id_num bigint,
  discord_id varchar(37),
  membership_level integer CHECK (membership_level >= 0 AND membership_level <= 6),
  join_date date,
  special_status varchar(50),
  previous_rsn varchar(12),
  alt_rsn TEXT [],
  on_leave boolean,
  active boolean,
  skill_comp_pts integer,
  skill_comp_pts_life integer,
  loc varchar(10),
  timezone varchar(10),
  notes varchar(512)
);

CREATE TABLE skill_comp
( 
    comp_id integer PRIMARY KEY,
    comp_name varchar(50),
    winner integer,
    CONSTRAINT fk_member_id
      FOREIGN KEY(winner) 
	  REFERENCES member(_id)
);