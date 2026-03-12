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
    'name': 'ATS Management',
    'version': '19.0.0.0.1',
    'category': 'Recruitment Maanagement',
    'sequence': 2,
    'website': 'https://www.alhodood.com/',
    'author': 'Alhodood Technologies',
    'summary': 'Recruitment Maanagement',
    'description': 'Recruitment Maanagement ',
    'depends': ['project','crm'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/project_views.xml',
        'views/applicant_stage_views.xml',
        'views/project_task.xml',
        'views/applicant_view.xml',
        'wizard/task_wizards.xml',
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
