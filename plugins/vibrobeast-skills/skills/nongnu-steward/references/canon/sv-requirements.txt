<?php
# Savannah hosting requirements.
#
# Copyright (C) 1999, 2000 The SourceForge Crew
# Copyright (C) 2003 Jaime E. Villate
# Copyright (C) 2000-2006 Mathieu Roy <yeupou--gnu.org>
# Copyright (C) 2005, 2006, 2010-2012 Michael J. Flickinger
# Copyright (C) 2014, 2016, 2017 Assaf Gordon
# Copyright (C) 2001-2011, 2013, 2017 Sylvain Beucler
# Copyright (C) 2008-2017, 2020 Karl Berry
# Copyright (C) 2005, 2020 Richard Stallman
# Copyright (C) 2013, 2014, 2017-2026 Ineiev
#
# This file is part of Savane.
#
# Code written before 2008-03-30 (commit 8b757b2565ff) is distributed
# under the terms of the GNU General Public license version 3 or (at your
# option) any later version; further contributions are covered by
# the GNU Affero General Public license version 3 or (at your option)
# any later version.  The license notices for the AGPL and the GPL follow.
#
# Savane is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# Savane is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# Savane is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# Savane is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
print '<p>'
  .  _("Please read these usage terms carefully.  If you don't follow them,\n"
       . "we will not accept your project; if we don't have enough "
       . "information\ndetermine whether your project follows these terms, we "
       . "will\nhave to ask you for more details.\nOnce your "
       . "project is accepted, you are expected to continue following\n"
       . "these terms.")
  . "</p>\n";
if (substr ($GLOBALS['sys_default_domain'], -8) == ".gnu.org")
  print '<p>'
    . sprintf (
        _("All packages registered in savannah.gnu.org (as opposed to "
          . "savannah.<em>non</em>gnu.org) are GNU packages,\nso they should "
          . "follow the <a href=\"%s\">GNU Coding Standards</a>."),
        '//www.gnu.org/prep/standards/'
      )
    . "</p>\n<p>"
    . _("Note that some parts of the GNU Coding standards are firm\n"
        . "requirements, while some are just preferences or suggestions.")
    . "</p>\n";

print "<p>"
  . _("Our intent is to provide a permanent home for all versions of your "
      . "project.\nWe do reserve the right, however, to discontinue hosting "
      . "a project.")

  . "</p>\n\n" . html_h (3, _('Use of project account'), 'usage')
  . "<p id='purpose'>";

printf (
  _("The space given to you on this server is given for the expressed\n"
    . "purpose of advancing free software that can run in free operating "
    . "systems,\ndocumenting such software, or creating free educational "
    . "textbooks.\nUsing it to host or advertise nonfree software is "
    . "considered harmful to\nfree software.  For more information, please "
    . "read the\n<a href=\"%s\">Philosophy of the GNU Project</a>."),
  "//www.gnu.org/philosophy/philosophy.html"
);

print "</p>\n<p id='no-removal'>"
  . _("In order to preserve history and complete transparency, we will not\n"
      . "remove projects that contain anything substantive.")
  . "</p>\n\n"
  . html_h (3, _('No dependencies on nonfree software'), 'nonfree-deps') . "<p>"
  . sprintf (
      _("To be hosted on Savannah, your project must be free software, and it\n"
        . "must be kept independent of any nonfree software.  The package "
        . "must\nnot refer the user to any nonfree software; in other words,\n"
        . "it must not say anything that in our judgment is likely to\n"
        . "lead or steer users towards any nonfree software.  In particular,\n"
        . "it must not automatically download or install any nonfree "
        . "software.\nFor more info, see <a href=\"%s\">References to "
        . "Non-Free Software and\nDocumentation</a> in the GNU Coding "
        . "Standards."),
      "//www.gnu.org/prep/standards/html_node/References.html"
    )
  . "</p>\n<p id='best-on-free'>"
  . _("The program should deliver its full functionality and convenience on a\n"
      . "completely free platform based on a free operating system, such as\n"
      . "GNU/Linux, working entirely with other free software.  Otherwise, it\n"
      . "would be an inducement to install nonfree operating systems or other\n"
      . "nonfree software.")
  . "</p>\n<p id='support-for-nonfree'>"
  . _("It is ok for the program to run on nonfree platforms or nonfree\n"
      . "operating systems, and to work with well-known nonfree applications,\n"
      . "in addition to working with free software, provided it gives the "
      . "free\nsoftware at least as good support as it gives to nonfree\n"
      . "counterparts.  In other words, at no time, in no way, should your\n"
      . "program put free software users at a disadvantage compared to those\n"
      . "willing to use proprietary software.")

  . "</p>\n\n" . html_h (3, _('Regarding Android phones'), 'android') . "<p>"
  . _("Projects running on\n"
      . "Replicant may be hosted on Savannah.  Projects having dependencies "
      . "on\nnonfree software, such as proprietary software drivers or "
      . "AndroidOS,\nare not permissible.")
  . "</p>\n\n" . html_h (3, _('No nonfree formats'), 'proprietary-formats')
  . "<p>"
  . _("Using a format such as Flash, RealPlayer and QuickTime, that can in\n"
      . "practice only be created or played using nonfree software is, in\n"
      . "effect, to recommend use of that nonfree player software.  When the\n"
      . "free software implementation is not as technically good as "
      . "the proprietary one, using\nsuch a format is also implicitly "
      . "recommending the nonfree version.\nTherefore, your package shouldn't "
      . "contain or recommend materials in\nthese nonfree formats.")

  . "</p>\n\n" . html_h (3, _('Advertisements'), 'ads') . "<p>"
  . _("In general, you may not advertise anything commercial on a site hosted\n"
      . "here.  However, as exceptions, you can point people to commercial\n"
      . "support offerings for your free software project, and you can "
      . "mention\nfan items about your free software project that you sell "
      . "directly to\nthe users.")

  . "</p>\n\n" . html_h (3, _('Speaking about free software'), 'speaking')
  . "<p id='free-sw'>"
  . _("Savannah is a free software hosting site: we host projects such as\n"
      . "yours for the sake of the ideals of freedom and community that the\n"
      . "free software movement stands for.  We offer Savannah hosting to "
      . "free\nsoftware packages, as free software packages; therefore, "
      . "please\ndescribe your package clearly as a free software package.  "
      . "Please\nlabel it as &ldquo;free software&rdquo; rather than as "
      . "&ldquo;open\nsource&rdquo;.")
  . "</p>\n<p id='gnu-linux'>"
  . _("Savannah is part of the GNU Project, developer of the free software\n"
      . "operating system GNU.  The GNU/Linux system (GNU with Linux as the\n"
      . "kernel) runs Savannah now.  While using our hosting services, please\n"
      . "acknowledge our work by referring to this system as "
      . "&ldquo;GNU/Linux,&rdquo; not\njust &ldquo;Linux,&rdquo; when you "
      . "mention it in connection with this\npackage.")
   . "</p>\n<p id='words-to-avoid'>";
printf (
  _("If you'd like to help correct other confusions, you can find some\n"
    . "suggestions in <a href=\"%s\">Words to Use with Care</a>."),
  '//www.gnu.org/philosophy/words-to-avoid.html'
);

print "</p>\n\n" . html_h (3, _('Project naming'), 'naming') . "<p>"
  . _("Project identifiers should be reasonably descriptive, rather than\n"
      . "terse abbreviations or confusingly general.  If we believe this to be "
      . "an\nissue, we will discuss it with you.")

  . "</p>\n\n" . html_h (3, _('Free software licenses'), 'licenses') . "<p>"

  . _("You will be presented with a choice of free software licenses for\n"
      . "your project.  For hosting on Savannah, you must use one of these\n"
      . "licenses, which give the freedom to anyone to use, study, copy, and\n"
      . "distribute the source code and distribute modified versions of it, "
      . "and\nwhich are compatible with the GNU GPL version 3 and any later "
      . "versions.\nWe recommend GPLv3-or-later; in\n"
      . "any case, we require the &ldquo;or any later version&rdquo; "
      . "formulation\nfor the GNU GPL, GNU AGPL, and GNU LGPL.  You will "
      . "remain the copyright\nholder of whatever you create for your "
      . "project.");
print "</p>\n<p id='manuals'>";
printf (
  _("For manuals, we recommend GNU FDL version X-or-later, where X is the\n"
      . "latest released version of the <a href=\"%s\">FDL</a>; other\n"
      . "licensing compatible with that is acceptable."),
   '//www.gnu.org/licenses/fdl.html'
);
print "</p>\n<p id='legal-notices'>";

printf (
  _("Proper legal notices should be applied to, at least, each source\n"
      . "(non-derived) file in your project.  For example, for the GPL, see "
      . "the\npage on <a href=\"%s\">How to Use GNU Licenses</a>.\n"
      . "In the case of binary source files, such as images,\n"
      . "it is ok for the license to be stated in a companion <tt>README</tt> "
      . "or\nsimilar file.  It is desirable for derived files to also include "
      . "legal\nnotices.  A copy of the full text of all applicable licenses "
      . "should also\nbe included in the project."),
   "//www.gnu.org/licenses/gpl-howto.html"
);

print "</p>\n<p id='other-licenses'>"
  . _("If you need to use another license that is not listed, let us know\n"
      . "and we, or most likely the FSF licensing group, will review these\n"
      . "requests on a case-by-case basis.  Software licenses must be\n"
      . "GPL-compatible.")
  . "</p>\n";
?>
