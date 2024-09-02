require 'middleman-syntax'

module Resources
  module Helpers

    STATUSES ||= {
      200 => '200 OK',
      201 => '201 Created',
      202 => '202 Accepted',
      204 => '204 No Content',
      205 => '205 Reset Content',
      301 => '301 Moved Permanently',
      302 => '302 Found',
      307 => '307 Temporary Redirect',
      304 => '304 Not Modified',
      401 => '401 Unauthorized',
      403 => '403 Forbidden',
      404 => '404 Not Found',
      405 => '405 Method not allowed',
      409 => '409 Conflict',
      422 => '422 Unprocessable Entity',
      500 => '500 Server Error',
      502 => '502 Bad Gateway'
    }

    def json(key)
      hash = get_resource(key)
      hash = yield hash if block_given?
      Middleman::Syntax::Highlighter.highlight(JSON.pretty_generate(hash), 'json').html_safe
    end

    def get_resource(key)
      hash = case key
        when Hash
          h = {}
          key.each { |k, v| h[k.to_s] = v }
          h
        when Array
          key
        else Resources.const_get(key.to_s.upcase)
      end
      hash
    end

    def text_html(response, status, head = {})
      hs = headers(status, head.merge('Content-Type' => 'text/html'))
      res = CGI.escapeHTML(response)
      hs + %(<pre class="body-response"><code>) + res + "</code></pre>"
    end

  end

  AUTH_TOKEN ||= {
    token: "lkja8*lkajsd*lkjas;ldkj8asd;kJASd811"
  }

  USER ||= {
    id: 1,
    username: 'bob',
    is_superuser: false,
    first_name: 'Bob',
    last_name: 'Tims',
    email: 'john@gmail.com',
    role: 'account_admin',
    resident_access: [],
    facility_user: {
      can_see_residents: true,
      can_see_staff: true
    }
  }

  USER_INVITE ||= {
      id: 1,
      email: 'tim@example.com',
      role: 'manager',
      status: 'sent',
      employee: 12,
      can_see_residents: true,
      can_see_staff: true
  }

   EXAMINATION_REQUEST ||= {
      id: 1,
      resident: 2,
      examiner: 1,
      status: 'sent'
  }

  TUTORIAL_VIDEO ||= {
      title: 'Tutorial Video',
      url: 'https://www.youtube.com/watch?v=H11s_dbHbCA',
      description: 'Video Description'
  }

  INVITE_RESP ||= {
    invited: [1, 2],
    no_phone: [4, 5]
}

  EMPLOYEE_DETAIL ||= {
    id: 1,
    full_name: "test user",
    phone_number: "",
    ssn: "",
    positions: [
        1,
        2
    ],
    first_name: "Roberta",
    last_name: "Wood",
    email: "",
    picture: nil,
    address: "",
    address2: "",
    city: "",
    state: "",
    zip_field: "",
    date_of_hire: "2019-02-18",
    date_of_birth: nil,
    receives_emails: false,
    facility: 82,
    user: 1
  }

  RESIDENT ||= {
    id: 106,
    first_name: "Test",
    last_name: "BDay",
    avatar: nil,
    date_of_birth: "1990-08-15",
    age: 28,
    sex: "",
    marital_status: "",
    is_active: true,
    room_number: "",
    bed: "",
    race: "",
    religion: "",
    ssn: "",
    date_of_admission: "2018-06-01",
    admitted_from: "",
    date_of_discharge: nil,
    discharged_to: "",
    discharge_reason: "",
    discharge_notes: "",
    personal_notes: "",
    contact_1_name: "",
    contact_1_relationship: "",
    contact_1_home_phone: "",
    contact_1_mobile_phone: "",
    contact_1_email: "",
    contact_1_address: "",
    contact_2_name: "",
    contact_2_relationship: "",
    contact_2_home_phone: "",
    contact_2_mobile_phone: "",
    contact_2_email: "",
    contact_2_address: "",
    primary_insurance: "",
    primary_insurance_number: "",
    medicaid_number: "",
    mma_plan: "",
    mma_number: "",
    drug_plan_name: "",
    drug_plan_number: "",
    case_worker_first_name: "",
    case_worker_last_name: "",
    case_worker_phone: "",
    has_completed_1823_on_file: false,
    form_1823_completed_date: nil,
    dnr_on_file: false,
    diagnosis: "",
    allergies: "",
    long_term_care_provider: "Aetna",
    long_term_care_provider_other: "",
    long_term_care_number: "",
    primary_doctor_name: "",
    primary_doctor_phone: "",
    permanent_placement: false,
    primary_doctor_address: "",
    primary_doctor_email: "",
    psychiatric_doctor_name: "",
    psychiatric_doctor_phone: "",
    psychiatric_doctor_address: "",
    psychiatric_doctor_email: "",
    medical_notes: "",
    dialysis_center: "",
    dialysis_center_phone: "",
    hospice_provider: "",
    hospice_provider_phone: "",
    has_signed_contract_on_file: false,
    contract_amount: "",
    has_durable_power_of_attorney_on_file: false,
    has_long_term_care_program: false,
    has_assistive_care_services: false,
    has_oss: false,
    financial_notes: "",
    height: "",
    weight: "",
    physical_or_sensory_limitations: "",
    cognitive_or_behavioral_status: "",
    nursing_treatment_therapy_service_requirements: "",
    special_precautions: "",
    is_elopement_risk: false,
    ambulation_status: "",
    bathing_status: "",
    dressing_status: "",
    eating_status: "",
    self_care_status: "",
    toileting_status: "",
    transferring_status: "",
    is_diet_regular: false,
    is_diet_calorie_controlled: false,
    is_diet_no_added_salt: false,
    is_diet_low_fat_or_low_cholesterol: false,
    is_diet_low_sugar: false,
    is_diet_other: false,
    diet_other_comments: "",
    has_communicable_disease: false,
    has_communicable_disease_comments: "",
    is_bedridden: false,
    is_bedridden_comments: "",
    has_pressure_sores: false,
    has_pressure_sores_comments: "",
    does_pose_danger: false,
    does_pose_danger_comments: "",
    requires_nursing_or_psychiatric_care: false,
    requires_nursing_or_psychiatric_care_comments: "",
    can_needs_be_met: false,
    can_needs_be_met_comments: "",
    preparing_meals_status: "",
    shopping_status: "",
    making_phone_call_status: "",
    handling_personal_affairs_status: "",
    handling_financial_affairs_status: "",
    section_2_a_other_name: "",
    section_2_a_other_status: "",
    section_2_a_other_comments: "",
    observing_wellbeing_status: "",
    observing_wellbeing_comments: "",
    observing_whereabouts_status: "",
    observing_whereabouts_comments: "",
    reminders_for_important_tasks_status: "",
    reminders_for_important_tasks_comments: "",
    section_2_b_other1_name: "",
    section_2_b_other1_status: "",
    section_2_b_other1_comments: "",
    section_2_b_other2_name: "",
    section_2_b_other2_status: "",
    section_2_b_other2_comments: "",
    section_2_b_other3_name: "",
    section_2_b_other3_status: "",
    section_2_b_other3_comments: "",
    section_2_b_other4_name: "",
    section_2_b_other4_status: "",
    section_2_b_other4_comments: "",
    additional_comments_or_observations: "",
    medications: [],
    requires_help_taking_medication: false,
    is_dialysis_patient: false,
    is_under_hospice_care: false,
    requires_help_with_self_administered_medication: false,
    requires_medication_administration: false,
    is_able_to_administer_without_assistance: false,
    section_2_b_additional_comments: "",
    signature_on_file: false,
    examiner_name: "",
    examiner_signature: nil,
    examiner_medical_license_number: "",
    examiner_address: "",
    examiner_phone: "",
    examiner_title: "",
    examination_date: nil,
    services_offered: [],
    gaurdian_or_recipient_name: "",
    gaurdian_or_recipient_signature: nil,
    administrator_or_designee_name: "",
    administrator_or_designee_signature: nil,
    examination_due_date: "2018-07-01",
    examination_interval: 1,
    examination_requested: true,
    primary_is_examiner: false,
    primary_is_examiner_invited: false,
    has_examiners_assigned: true
  }

  TASK ||= [{
      id: 8251,
      employee: {
          id: 167,
          first_name: "Test",
          last_name: "User",
          full_name: "Twest User"
      },
      type: {
          id: 36,
          name: "Added to AHCA Facilities Background Check Roster",
          required_within: "0 seconds",
          validity_period: "0 seconds",
          course: 1,
          is_one_off: true,
          is_training: false,
          is_continuing_education: false,
          required_for: [],
          rule: ''
      },
      status_name: "Open",
      scheduled_event: nil,
      due_date: "2019-02-18",
      status: 1,
      antirequisite: nil
  }]

  TASK_OBJECT ||= {
    count: 1,
    results:  [{
      id: 8251,
      employee: {
          id: 167,
          first_name: "Test",
          last_name: "User",
          full_name: "Twest User"
      },
      type: {
          id: 36,
          name: "Added to AHCA Facilities Background Check Roster",
          required_within: "0 seconds",
          validity_period: "0 seconds",
          is_one_off: true,
          is_training: false,
          course: {
              id: 1,
              task_type: 1,
              name: "course 1",
              description: "asdf",
              objective: "sadf",
              duration: "",
              published: true,
              items: [
                  2,
                  1
              ]
          },
          is_continuing_education: false,
          required_for: [],
          rule: ''
      },
      status_name: "Open",
      scheduled_event: nil,
      due_date: "2019-02-18",
      status: 1,
      antirequisite: nil
  }]
}

TASK_EXPANDED ||= [{
    id: 8251,
    employee: {
        id: 167,
        first_name: "Test",
        last_name: "User",
        full_name: "Twest User"
    },
    type: {
        id: 36,
        name: "Added to AHCA Facilities Background Check Roster",
        required_within: "0 seconds",
        validity_period: "0 seconds",
        course: {
            id: 1,
            task_type: 1,
            name: "course 1",
            description: "asdf",
            objective: "sadf",
            duration: "",
            published: true,
            items: [
              {
                id: 1,
                course: 1,
                title: "messy item",
                order: 1,
                image: {
                  full_size: "https://api.staging.alfboss.com/media/trainings/course-item-images/2c0c2666-454c-4f58-a47f-35cf47d636b2.jpg"
                },
                texts: [
                  {
                    id: 1,
                    item: 1,
                    question: "Lorem ipsum dolor sit",
                    answer: "Lorem ipsum dolor sit",
                    order: 0
                  },
                  {
                    id: 2,
                    item: 2,
                    question: "Lorem ipsum dolor sit",
                    answer: "Lorem ipsum dolor sit",
                    order: 1
                  }
                ],
                letter_size_image: [
                  {
                    id: 1,
                    item: 1,
                    image: {
                      "full_size": "http://api.alfboss.local/media/trainings/course-letter-size-images/2ddc708d-e21e-471c-a7b4-4c6d1339f770.jpg"
                    }
                  },
                  {
                    id: 2,
                    item: 2,
                    image: {
                      "full_size": "http://api.alfboss.local/media/trainings/course-letter-size-images/2ddc708d-e21e-471c-a7b4-4c6d1339f770.jpg"
                    }
                  }
                ],
                videos: [
                  {
                    id: 1,
                    item: 1,
                    order: 0,
                    link: "https://northlake1222.wistia.com/medias/zj31woo6zr",
                    video_id: "zj31woo6zr",
                    thumbnail: {
                      "full_size": "http://api.alfboss.local/media/trainings/course-item-video-thumbnail/2ddc708d-e21e-471c-a7b4-4c6d1339f770.jpg"
                    },
                    embedded_url: "<script src=\"https://fast.wistia.com/embed/medias/zj31woo6zr.jsonp\"</div>",
                  }
                ]
              }
            ]
        },
        is_one_off: true,
        is_training: false,
        is_continuing_education: false,
        required_for: [],
        rule: ''
    },
    status_name: "Open",
    scheduled_event: nil,
    due_date: "2019-02-18",
    status: 1,
    antirequisite: nil
}]

TASK_HISTORY ||= {
  id: 325,
  employee: {
      id: 167,
      first_name: "Test",
      last_name: "User",
      full_name: "Test User"
  },
  type: {
      id: 32,
      name: "2 hr Pre-Service Orientation",
      required_within: "0 seconds",
      validity_period: "0 seconds",
      course: 1,
      is_one_off: true,
      is_training: true,
      is_continuing_education: false,
      required_for: [
          12
      ],
      rule: "Effective 10/1/15, new employees (who have not completed core training) must\r\nattend a two-hour pre-service orientation before interacting with residents.\r\nTopics must help employees provide responsible care and respect resident needs.\r\nEmployees and the administrator must sign a statement of completion and the\r\nstatement must be maintained in each employee’s file.\r\n\r\nfor details of legislation: http://elderaffairs.state.fl.us/doea/press/2015/HB_1001_letter_for_Providers.pdf"
  },
  status_name: "Completed",
  certificate: nil,
  completion_date: "2019-02-18",
  expiration_date: "2019-02-18",
  status: 2,
  credit_hours: 0.0,
  antirequisite: nil
}

TASK_HISTORY_OBJECT ||= {
  count: 1,
  results: [
    {
      id: 325,
      employee: {
          id: 167,
          first_name: "Test",
          last_name: "User",
          full_name: "Test User"
      },
      type: {
          id: 32,
          name: "2 hr Pre-Service Orientation",
          required_within: "0 seconds",
          validity_period: "0 seconds",
          is_one_off: true,
          is_training: true,
          is_continuing_education: false,
          required_for: [
              12
          ],
          rule: "Effective 10/1/15, new employees (who have not completed core training) must\r\nattend a two-hour pre-service orientation before interacting with residents.\r\nTopics must help employees provide responsible care and respect resident needs.\r\nEmployees and the administrator must sign a statement of completion and the\r\nstatement must be maintained in each employee’s file.\r\n\r\nfor details of legislation: http://elderaffairs.state.fl.us/doea/press/2015/HB_1001_letter_for_Providers.pdf"
      },
      status_name: "Completed",
      certificate: nil,
      completion_date: "2019-02-18",
      expiration_date: "2019-02-18",
      status: 2,
      credit_hours: 0.0,
      antirequisite: nil
    }
  ]
}

TASK_HISTORY_EXPANDED ||= {
  id: 325,
  employee: {
      id: 167,
      first_name: "Test",
      last_name: "User",
      full_name: "Test User"
  },
  type: {
      id: 32,
      name: "2 hr Pre-Service Orientation",
      required_within: "0 seconds",
      validity_period: "0 seconds",
      course: {
          id: 1,
          task_type: 1,
          name: "course 1",
          description: "asdf",
          objective: "sadf",
          duration: "",
          published: true,
          items: [
              {
                id: 1,
                course: 1,
                title: "messy item",
                order: 1,
                image: {
                  full_size: "https://api.staging.alfboss.com/media/trainings/course-item-images/2c0c2666-454c-4f58-a47f-35cf47d636b2.jpg"
                },
                texts: [
                  {
                    id: 1,
                    item: 1,
                    question: "Lorem ipsum dolor sit",
                    answer: "Lorem ipsum dolor sit",
                    order: 0
                  },
                  {
                    id: 2,
                    item: 2,
                    question: "Lorem ipsum dolor sit",
                    answer: "Lorem ipsum dolor sit",
                    order: 1
                  }
                ],
                letter_size_image: [
                  {
                    id: 1,
                    item: 1,
                    image: {
                      "full_size": "http://api.alfboss.local/media/trainings/course-letter-size-images/2ddc708d-e21e-471c-a7b4-4c6d1339f770.jpg"
                    }
                  },
                  {
                    id: 2,
                    item: 2,
                    image: {
                      "full_size": "http://api.alfboss.local/media/trainings/course-letter-size-images/2ddc708d-e21e-471c-a7b4-4c6d1339f770.jpg"
                    }
                  }
                ],
                videos: [
                  {
                    id: 1,
                    item: 1,
                    order: 0,
                    link: "https://northlake1222.wistia.com/medias/zj31woo6zr",
                    video_id: "zj31woo6zr",
                    thumbnail: {
                      "full_size": "http://api.alfboss.local/media/trainings/course-item-video-thumbnail/2ddc708d-e21e-471c-a7b4-4c6d1339f770.jpg"
                    },
                    embedded_url: "<script src=\"https://fast.wistia.com/embed/medias/zj31woo6zr.jsonp\"</div>",
                  }
                ]
              }
            ]
      },
      is_one_off: true,
      is_training: true,
      is_continuing_education: false,
      required_for: [
          12
      ],
      rule: "Effective 10/1/15, new employees (who have not completed core training) must\r\nattend a two-hour pre-service orientation before interacting with residents.\r\nTopics must help employees provide responsible care and respect resident needs.\r\nEmployees and the administrator must sign a statement of completion and the\r\nstatement must be maintained in each employee’s file.\r\n\r\nfor details of legislation: http://elderaffairs.state.fl.us/doea/press/2015/HB_1001_letter_for_Providers.pdf"
  },
  status_name: "Completed",
  certificate: nil,
  completion_date: "2019-02-18",
  expiration_date: "2019-02-18",
  status: 2,
  credit_hours: 0.0,
  antirequisite: nil
}

FACILITY ||= {
  address_city: "Test city",
  address_line1: "Test address",
  address_line2: "Test address line 2",
  address_zipcode: "12345",
  alzheimer: false,
  bought_ebook: false,
  businessagreement: nil,
  can_use_subscription_trial: false,
  capacity: 2,
  contact_email: "test@test.com",
  contact_phone: "(111) 111-1111",
  contact_fax: "(111) 111-1111",
  default: {id: 18, employee_responsibility: -1, facility: 18},
  directory_facility: 1,
  first_aid_cpr: false,
  has_active_subscription: true,
  has_active_trainings_subscription: true,
  id: 18,
  is_resident_module_enabled: true,
  is_staff_module_enabled: true,
  name: "test",
  primary_administrator_name: "test test",
  questions: [
    {
      id: 1,
      rules: [
        {
          id: 2,
          facility_question: 5,
          position: 8,
          responsibility: 25,
        }
      ],
      question: "Question",
      is_license: false,
      description: "Does your administrator have AIDS/HIV?",
      slug: "question2"
    }
  ],
  state: "AZ",
  is_lms_module_enabled: false,
  npi: "",
  admin_signature: "data:image/png;base64,"
}

CURRENT_USER ||= {
  user: USER,
  facility: FACILITY
}

TASK_TYPE ||= [{ 
  id: 25,
  required_within: "12 weeks",
  validity_period: "0 seconds",
  is_continuing_education: false,
  required_for: [
      {
          id: 6,
          name: "Provides Special Care for Persons with Alzheimer's"
      }
  ],
  course: {
      id: 1,
      task_type: 1,
      name: "course 1",
      description: "asdf",
      objective: "sadf",
      duration: "",
      published: true,
      items: [
          2,
          1
      ]
  },
  prerequisites: [],
  education_credits: [],
  education_requirements: [],
  name: "Alzheimer's Training 1",
  is_training: true,
  hide_in_lms: true,
  is_one_off: true,
  rule: "",
  image: {
      full_size: "https://api.alfboss.local/media/48123038_2405742919439072_622331892082933760_n.jpg"
  },
  required_after_task_type: nil,
  facility: nil,
  supersedes: []
}]

COURSE ||= {
  id: 1,
  task_type: 1,
  name: "course 1",
  description: "testing",
  objective: "testing",
  published: false,
  minimum_score: 2,
  language: 1,
  max_points: 4,
  items: [
      1,
      2,
      3,
      31
  ],
  course_taken: [
            {
          id: 8,
          employee: 181,
          course: 2,
          status: 1,
          status_name: "Completed",
          score: 22,
          start_date: "2019-03-31",
          completed_date: "2019-04-01"
      }
  ],
  last_started_course_item: 9,
  statement_required: false
}

COURSE_LAST_STARTED_NULL ||= {
  id: 1,
  task_type: 1,
  name: "course 1",
  description: "testing",
  objective: "testing",
  published: false,
  minimum_score: 2,
  language: 1,
  max_points: 4,
  items: [
      1,
      2,
      3,
      31
  ],
  course_taken: [
            {
          id: 8,
          employee: 181,
          course: 2,
          status: 1,
          status_name: "Completed",
          score: 22,
          start_date: "2019-03-31",
          completed_date: "2019-04-01"
      }
  ],
  last_started_course_item: nil
}



EMPLOYEE_COURSE ||= {
  id: 9,
  employee: 181,
  course: 2,
  status: 0,
  score: 12,
  start_date: "2019-03-31",
  completed_date: "2019-04-01"
}

COURSE_ITEM ||= {
  id: 1,
  course: 1,
  title: "title 1",
  image: {
    full_size: "https://api.staging.alfboss.com/media/trainings/course-item-images/2c0c2666-454c-4f58-a47f-35cf47d636b2.jpg"
  },
  texts: [
      1,
      2,
      3,
      31
  ],
  videos: [
      3,
      2,
      1
  ],
  boolean: [
      1,
      2,
      3
  ],
  letter_size_image: [
      1
  ],
  choices: [
      1,
      2,
      3,
      15,
      16
  ],
  started_at: "2019-05-29T00:00:00Z",
  min_duration: 10
}

OPEN_COURSE_RESPONSE ||= {
  id: 9,
  duration: "120",
  description: "Lorem Ipsum is simply dummy text of the printing and typesetting industry.",
  objective: "Objective text",
  name: "Alz Training 1",
  items: [67,34,56],
  last_started_course_item: 34,
  language: 1,
  published: true,
  minimum_score: 10,
  statement_required: true,
  task: {
    id: 128411,
    type: {
      id: 25,
      image: {
        full_size: "image-url"
      }
    }
  }
}

COURSE_ITEM_TEXT ||= {
  id: 1,
  item: 1,
  question: "question 1",
  answer: "answer 1",
  order: 0
}

COURSE_ITEM_VIDEO ||= {
  id: 1,
  item: 1,
  link: "example.com",
  embedded_url: "example.com",
  answer: "answer 1",
  order: 0
}

COURSE_ITEM_BOOLEAN ||= {
  id: 1,
  item: 1,
  question: "question 1",
  answer: true,
  order: 0
}

COURSE_ITEM_LETTER_SIZE_IMAGE ||= {
  id: 1,
  item: 1,
  image: {full_size: "https://api.staging.alfboss.com/media/trainings/course-item-images/2c0c2666-454c-4f58-a47f-35cf47d636b2.jpg"},
  order: 0
}

COURSE_ITEM_MULTI_CHOICE ||= {
  id: 1,
  item: 1,
  question: "question 8",
  options: [
      1,
      2,
      3
  ],
  answers: [
      2,
      3,
      37
  ],
  order: 2
}

MULTI_CHOICE_OPTION ||= {
  id: 1,
  label: "option 1"
}

EMPLOYEE_COURSE_ITEM ||= {
  id: 9,
  employee: 181,
  course_item: 2,
  started_at: "2019-05-29T00:00:00Z"
}

SPONSORSHIP ||= {
  id: 1,
  name: "Sponsorship name",
  banner_1: {
    "full_size": "http://api.alfboss.local:8000/media/trainings/sponsorships/banner_1/9db8ebfc-8687-4a07-8268-11711e53a326.png"
  },
  url_1: "http://tsl.io/",
  banner_2: nil,
  url_2: ''
}

BED_HOLD ||= {
  id: 1,
  resident: 2,
  date_out: "2019-06-29",
  date_in: "2019-06-30",
  notes: "Some text",
  sent_to: "Some text"
}

RESIDENT_CLOUDCARE_RESPONSE ||= {
  id: 133,
  first_name: "John",
  last_name: "Doe",
  date_of_birth: "1995-03-04",
  sex: "m",
  date_of_admission: "2021-01-13",
  ssn: "111-22-2222",
  facility: 13,
  primary_insurance: "MediCare",
  insurance_relationship: "self",
  insured_first_name: "John",
  insured_last_name: "Doe",
  insurance_policy_type: "primary",
  insured_id: 123452
}

EMPLOYEE_CLOUDCARE_RESPONSE ||= {
  id: 312,
  first_name: "John",
  last_name: "Doe",
  positions_detail: [
      {
          id: 9,
          name: "Manager"
      }
  ],
  facility: 96,
  date_of_hire: "2021-01-14"
}

FACILITY_CLOUDCARE_RESPONSE ||= [
  {
    id: 1,
    name: "Facility 1"
  },
  {
    id: 2,
    name: "Facility 2"
  },
]

POSITION_CLOUDCARE_RESPONSE ||= [
  {
    id: 1,
    name: "Administrator"
  },
  {
    id: 2,
    name: "Asst. Administrator"
  },
]


end

include Resources::Helpers
