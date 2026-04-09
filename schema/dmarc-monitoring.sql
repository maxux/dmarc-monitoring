--
-- Tables
--

CREATE TABLE `dmarc_reports` (
  `id` int(11) NOT NULL,
  `receiver` varchar(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `received` timestamp NOT NULL,
  `parsed` timestamp NOT NULL,
  `filename` varchar(128) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `rdate` date NOT NULL,
  `orgname` varchar(48) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `reportid` varchar(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

CREATE TABLE `dmarc_reports_policy` (
  `rid` int(11) NOT NULL,
  `domain` varchar(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `adkim` tinyint(4) NOT NULL,
  `aspf` tinyint(4) NOT NULL,
  `policy` tinyint(4) NOT NULL,
  `subpolicy` tinyint(4) DEFAULT NULL,
  `percent` tinyint(4) NOT NULL

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

CREATE TABLE `dmarc_reports_records` (
  `id` int(11) NOT NULL,
  `rid` int(11) NOT NULL,
  `source` varchar(40) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `eamount` mediumint(9) NOT NULL,
  `edisp` tinyint(4) NOT NULL,
  `edkim` tinyint(4) NOT NULL,
  `espf` tinyint(4) NOT NULL,
  `ereason` tinyint(4) DEFAULT NULL,
  `ecomment` varchar(64) CHARACTER SET ascii COLLATE ascii_bin DEFAULT NULL,
  `mailfrom` varchar(32) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `mailto` varchar(32) CHARACTER SET ascii COLLATE ascii_bin DEFAULT NULL,
  `dkimdom` varchar(72) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `dkimresult` tinyint(4) NOT NULL,
  `spfdom` varchar(72) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `spfresult` tinyint(4) NOT NULL

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

CREATE TABLE `dmarc_resources` (
  `filename` varchar(128) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  `report` blob NOT NULL

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

CREATE TABLE `dmarc_types` (
  `id` tinyint(4) NOT NULL,
  `rkey` varchar(24) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `name` varchar(32) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `severity` varchar(16) CHARACTER SET ascii COLLATE ascii_bin NOT NULL

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

--
-- Primary Keys
--

ALTER TABLE `dmarc_reports`
  ADD PRIMARY KEY (`id`),
  ADD KEY `filename` (`filename`),
  ADD KEY `rdate` (`rdate`);

ALTER TABLE `dmarc_reports_policy`
  ADD PRIMARY KEY (`rid`),
  ADD KEY `policy` (`policy`),
  ADD KEY `subpolicy` (`subpolicy`),
  ADD KEY `aspf` (`aspf`),
  ADD KEY `adkim` (`adkim`);

ALTER TABLE `dmarc_reports_records`
  ADD PRIMARY KEY (`id`),
  ADD KEY `edisp` (`edisp`),
  ADD KEY `edkim` (`edkim`),
  ADD KEY `espf` (`espf`),
  ADD KEY `ereason` (`ereason`),
  ADD KEY `dkimresult` (`dkimresult`),
  ADD KEY `spfresult` (`spfresult`),
  ADD KEY `rid` (`rid`);

ALTER TABLE `dmarc_resources`
  ADD PRIMARY KEY (`filename`);

ALTER TABLE `dmarc_types`
  ADD PRIMARY KEY (`id`);

ALTER TABLE `dmarc_reports`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

ALTER TABLE `dmarc_reports_records`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

ALTER TABLE `dmarc_types`
  MODIFY `id` tinyint(4) NOT NULL AUTO_INCREMENT;

--
-- Constraints
--

ALTER TABLE `dmarc_reports`
  ADD CONSTRAINT `dmarc_reports_ibfk_1` FOREIGN KEY (`filename`) REFERENCES `dmarc_resources` (`filename`);

ALTER TABLE `dmarc_reports_policy`
  ADD CONSTRAINT `dmarc_reports_policy_ibfk_1` FOREIGN KEY (`policy`) REFERENCES `dmarc_types` (`id`),
  ADD CONSTRAINT `dmarc_reports_policy_ibfk_2` FOREIGN KEY (`subpolicy`) REFERENCES `dmarc_types` (`id`),
  ADD CONSTRAINT `dmarc_reports_policy_ibfk_3` FOREIGN KEY (`aspf`) REFERENCES `dmarc_types` (`id`),
  ADD CONSTRAINT `dmarc_reports_policy_ibfk_4` FOREIGN KEY (`adkim`) REFERENCES `dmarc_types` (`id`),
  ADD CONSTRAINT `dmarc_reports_policy_ibfk_5` FOREIGN KEY (`rid`) REFERENCES `dmarc_reports` (`id`);

ALTER TABLE `dmarc_reports_records`
  ADD CONSTRAINT `dmarc_reports_records_ibfk_1` FOREIGN KEY (`edisp`) REFERENCES `dmarc_types` (`id`),
  ADD CONSTRAINT `dmarc_reports_records_ibfk_2` FOREIGN KEY (`edkim`) REFERENCES `dmarc_types` (`id`),
  ADD CONSTRAINT `dmarc_reports_records_ibfk_3` FOREIGN KEY (`espf`) REFERENCES `dmarc_types` (`id`),
  ADD CONSTRAINT `dmarc_reports_records_ibfk_4` FOREIGN KEY (`ereason`) REFERENCES `dmarc_types` (`id`),
  ADD CONSTRAINT `dmarc_reports_records_ibfk_5` FOREIGN KEY (`dkimresult`) REFERENCES `dmarc_types` (`id`),
  ADD CONSTRAINT `dmarc_reports_records_ibfk_6` FOREIGN KEY (`spfresult`) REFERENCES `dmarc_types` (`id`),
  ADD CONSTRAINT `dmarc_reports_records_ibfk_7` FOREIGN KEY (`rid`) REFERENCES `dmarc_reports` (`id`);

--
-- Types Initial Data
--

INSERT INTO `dmarc_types` (`id`, `rkey`, `name`, `severity`) VALUES
(1, 'none', 'none', 'info'),
(2, 'reject', 'reject', 'info'),
(3, 'quarantine', 'quarantine', 'info'),
(4, 'pass', 'pass', 'info'),
(5, 'fail', 'fail', 'info'),
(6, 'relaxed', 'relaxed', 'info'),
(7, 'strict', 'strict', 'info'),
(8, 'forwarded', 'forwarded', 'info'),
(9, 'local_policy', 'local_policy', 'info'),
(10, 'mailing_list', 'mailing_list', 'info'),
(11, 'other', 'other', 'info'),
(12, 'sampled_out', 'sampled_out', 'info'),
(13, 'trusted_forwarder', 'trusted_forwarder', 'info'),
(14, 'policy', 'policy', 'info'),
(15, 'neutral', 'neutral', 'info'),
(16, 'temperror', 'temperror', 'info'),
(17, 'permerror', 'permerror', 'info'),
(18, 'softfail', 'softfail', 'info');
