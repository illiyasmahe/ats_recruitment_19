# -*- coding: utf-8 -*-
#############################################################################

#    Alhodood Technologies.
#
#    Copyright (C) 2026-TODAY Alhodood Technologies(<https://www.alhodood.com>)
#    Author: Alhodood Technologies(<https://www.alhodood.com>)
#
#    You can modify it under the terms of the GNU Affero General Public License
#    (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License (AGPL v3) for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
{
    'name': 'ATS Website Jobs',
    'version': '19.0.0.0.0',
    'category': 'Job listing and application portal',
    'sequence': 2,
    'website': 'https://www.alhodood.com/',
    'author': 'Alhodood Technologies',
    'summary': 'Recruitment Maanagement',
    'description': 'Recruitment Maanagement ',
    'depends': ['website','project','ats_tracking'],
    'data': [
        'views/website_menu.xml',
        'views/job_templates.xml',
        'views/res_config_settings_view.xml',
    ],
    'demo': [
    ],
    'assets': {

    },
    'external_dependencies': {

    },
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
